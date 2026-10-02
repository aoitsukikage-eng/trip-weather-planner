"""Unit tests for TTLCache and AsyncSingleFlight primitive."""

from __future__ import annotations

import asyncio

import pytest

from app.core.cache import AsyncSingleFlight, CacheStatus, TTLCache


def test_ttl_cache_fresh_hit():
    current_time = 1000.0
    cache = TTLCache(default_ttl=60, stale_retention=3600, clock=lambda: current_time)

    cache.set("key1", "val1")
    # Fresh lookup
    assert cache.get("key1") == "val1"
    entry = cache.get_entry("key1")
    assert entry.status == CacheStatus.FRESH.value
    assert entry.value == "val1"
    assert entry.is_fresh is True
    assert entry.is_stale is False
    assert entry.is_miss is False


def test_ttl_cache_stale_lookup_and_get_compatibility():
    current_time = 1000.0
    cache = TTLCache(default_ttl=60, stale_retention=3600, clock=lambda: current_time)

    cache.set("key1", "val1")

    # Advance beyond fresh TTL (60s) but within stale retention (3600s)
    current_time = 1070.0

    # get() must retain fresh-only compatibility and return None
    assert cache.get("key1") is None

    # Explicit lookup must identify stale state
    entry = cache.get_entry("key1")
    assert entry.status == CacheStatus.STALE.value
    assert entry.value == "val1"
    assert entry.is_fresh is False
    assert entry.is_stale is True
    assert entry.is_miss is False
    assert cache.get_stale("key1") == "val1"

    # Verify entry is NOT lazily evicted while still in stale retention
    assert len(cache) == 1


def test_ttl_cache_miss_after_stale_retention_and_lazy_cleanup():
    current_time = 1000.0
    cache = TTLCache(default_ttl=60, stale_retention=3600, clock=lambda: current_time)

    cache.set("key1", "val1")

    # Advance past fresh TTL + stale retention (60 + 3600 = 3660s)
    current_time = 1000.0 + 3661.0

    # Lookups should now be misses
    assert cache.get("key1") is None
    assert len(cache) == 0  # lazily cleaned up!

    cache.set("key2", "val2")
    current_time += 4000.0
    entry = cache.get_entry("key2")
    assert entry.status == CacheStatus.MISS.value
    assert entry.value is None
    assert entry.is_miss is True
    assert len(cache) == 0  # lazily cleaned up!


def test_ttl_cache_clear_and_delete():
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2

    assert cache.delete("a") is True
    assert cache.delete("a") is False
    assert cache.get("a") is None
    assert cache.get("b") == 2

    cache.clear()
    assert len(cache) == 0


@pytest.mark.asyncio
async def test_single_flight_coalescing_same_key():
    sf = AsyncSingleFlight()
    call_count = 0

    async def work(x: int) -> int:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        return x * 10

    results = await asyncio.gather(
        sf.run("k1", work, 3),
        sf.run("k1", work, 3),
        sf.run("k1", work, 3),
    )
    assert results == [30, 30, 30]
    assert call_count == 1
    assert sf.is_inflight("k1") is False


@pytest.mark.asyncio
async def test_single_flight_different_keys_independent():
    sf = AsyncSingleFlight()
    call_counts = {"k1": 0, "k2": 0}

    async def work(key: str) -> str:
        call_counts[key] += 1
        await asyncio.sleep(0.05)
        return f"done-{key}"

    r1, r2 = await asyncio.gather(
        sf.run("k1", work, "k1"),
        sf.run("k2", work, "k2"),
    )
    assert r1 == "done-k1"
    assert r2 == "done-k2"
    assert call_counts["k1"] == 1
    assert call_counts["k2"] == 1


@pytest.mark.asyncio
async def test_single_flight_leader_exception():
    sf = AsyncSingleFlight()

    async def failing_work():
        await asyncio.sleep(0.02)
        raise RuntimeError("upstream exploded")

    t1 = asyncio.create_task(sf.run("err", failing_work))
    t2 = asyncio.create_task(sf.run("err", failing_work))

    results = await asyncio.gather(t1, t2, return_exceptions=True)
    assert isinstance(results[0], RuntimeError)
    assert str(results[0]) == "upstream exploded"
    assert isinstance(results[1], RuntimeError)
    assert str(results[1]) == "upstream exploded"
    # Verify cleanup on exception
    assert sf.is_inflight("err") is False

    # Subsequent caller should be able to run and succeed
    async def ok_work():
        return "recovered"

    assert await sf.run("err", ok_work) == "recovered"


@pytest.mark.asyncio
async def test_single_flight_waiter_cancellation_does_not_cancel_leader():
    sf = AsyncSingleFlight()
    leader_started = asyncio.Event()

    async def slow_work():
        leader_started.set()
        await asyncio.sleep(0.1)
        return "leader_result"

    leader_coro = sf.run("cancel_waiter", slow_work)
    waiter_coro = sf.run("cancel_waiter", slow_work)

    leader_task = asyncio.create_task(leader_coro)
    await leader_started.wait()
    waiter_task = asyncio.create_task(waiter_coro)

    # Cancel waiter
    await asyncio.sleep(0.01)
    waiter_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await waiter_task

    # Leader should continue and finish successfully
    res = await leader_task
    assert res == "leader_result"
    assert sf.is_inflight("cancel_waiter") is False


@pytest.mark.asyncio
async def test_single_flight_leader_task_cancelled():
    sf = AsyncSingleFlight()
    started = asyncio.Event()

    async def slow():
        started.set()
        await asyncio.sleep(1.0)
        return "done"

    t1 = asyncio.create_task(sf.run("cancel_leader", slow))
    await started.wait()
    t2 = asyncio.create_task(sf.run("cancel_leader", slow))

    # Cancel the underlying leader task
    underlying_task = sf._inflight["cancel_leader"]
    underlying_task.cancel()

    res = await asyncio.gather(t1, t2, return_exceptions=True)
    assert all(isinstance(r, asyncio.CancelledError) for r in res)
    assert sf.is_inflight("cancel_leader") is False

    # Verify state clean and next call works
    assert await sf.run("cancel_leader", lambda: asyncio.sleep(0.01, result="new")) == "new"


@pytest.mark.asyncio
async def test_single_flight_leader_caller_cancellation_preserves_task_for_waiter():
    sf = AsyncSingleFlight()
    started = asyncio.Event()

    async def slow():
        started.set()
        await asyncio.sleep(0.05)
        return "shielded_result"

    leader_coro = sf.run("leader_caller_cancel", slow)
    leader_task = asyncio.create_task(leader_coro)
    await started.wait()

    waiter_task = asyncio.create_task(sf.run("leader_caller_cancel", slow))

    # Cancel the leader's outer caller task
    leader_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await leader_task

    # The waiter should still receive the result because the background task is shielded
    waiter_res = await waiter_task
    assert waiter_res == "shielded_result"
    assert sf.is_inflight("leader_caller_cancel") is False


@pytest.mark.asyncio
async def test_single_flight_all_waiters_cancelled_cancels_underlying_task():
    sf = AsyncSingleFlight()
    underlying_cancelled = False

    async def slow():
        nonlocal underlying_cancelled
        try:
            await asyncio.sleep(5.0)
            return "done"
        except asyncio.CancelledError:
            underlying_cancelled = True
            raise

    t = asyncio.create_task(sf.run("cancel_all", slow))
    await asyncio.sleep(0.01)
    t.cancel()
    with pytest.raises(asyncio.CancelledError):
        await t

    await asyncio.sleep(0.01)
    assert underlying_cancelled is True
    assert sf.is_inflight("cancel_all") is False
