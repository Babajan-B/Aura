package com.auraguard.phone.ml

/**
 * Thread-safe circular buffer of FloatArrays.
 *
 * Each slot holds one second's worth of feature vectors so that 10 slots ==
 * a 10-second analysis window — matching the model's signal context.
 *
 * - [push] is O(1) and silently overwrites the oldest entry when full.
 * - [snapshot] returns a copy in chronological order.
 * - [flatten] concatenates all slots into a single FloatArray for the model.
 */
class RingBuffer(
    private val capacity: Int = DEFAULT_CAPACITY,
    private val slotSize: Int,
) {
    private val slots: Array<FloatArray?> = arrayOfNulls(capacity)
    private var head: Int = 0
    private var size: Int = 0
    private val lock = Any()

    val isFull: Boolean get() = synchronized(lock) { size == capacity }
    val count: Int get() = synchronized(lock) { size }

    fun push(values: FloatArray) {
        require(values.size == slotSize) {
            "RingBuffer slotSize=$slotSize, got ${values.size}"
        }
        synchronized(lock) {
            slots[head] = values.copyOf()
            head = (head + 1) % capacity
            if (size < capacity) size++
        }
    }

    fun clear() = synchronized(lock) {
        for (i in slots.indices) slots[i] = null
        head = 0
        size = 0
    }

    /** Chronological copy of every populated slot. */
    fun snapshot(): List<FloatArray> = synchronized(lock) {
        if (size == 0) return emptyList()
        val start = if (size < capacity) 0 else head
        return List(size) { i ->
            slots[(start + i) % capacity]!!.copyOf()
        }
    }

    /** Concatenates [snapshot] into a single FloatArray sized capacity*slotSize. */
    fun flatten(): FloatArray {
        val snap = snapshot()
        val out = FloatArray(capacity * slotSize)
        for ((i, slot) in snap.withIndex()) {
            System.arraycopy(slot, 0, out, i * slotSize, slot.size)
        }
        return out
    }

    companion object { const val DEFAULT_CAPACITY = 10 }
}
