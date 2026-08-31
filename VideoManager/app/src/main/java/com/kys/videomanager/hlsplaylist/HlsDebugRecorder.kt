package com.kys.videomanager.hlsplaylist

class HlsDebugRecorder(private val maxEvents: Int = 80) {
    private val events = ArrayDeque<String>()

    @Synchronized
    fun record(label: String, value: String?) {
        if (value.isNullOrBlank()) return

        val compactValue = value
            .replace('\n', ' ')
            .replace(Regex("\\s+"), " ")
            .take(MAX_EVENT_LENGTH)
        events.addLast("$label: $compactValue")
        while (events.size > maxEvents) {
            events.removeFirst()
        }
    }

    @Synchronized
    fun clear() {
        events.clear()
    }

    @Synchronized
    fun snapshot(): String =
        if (events.isEmpty()) {
            "runtime debug events: 0"
        } else {
            buildString {
                appendLine("runtime debug events: ${events.size}")
                events.forEachIndexed { index, event ->
                    appendLine("debug[$index]: $event")
                }
            }.trimEnd()
        }

    private companion object {
        private const val MAX_EVENT_LENGTH = 800
    }
}
