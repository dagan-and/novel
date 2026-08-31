package com.kys.videomanager.video

data class VideoSourceDeletionSummary(
    val deletedCount: Int,
    val failedCount: Int
)

object VideoSourceDeletionPolicy {
    fun deleteImportedSources(
        sourceCount: Int,
        deleteSourceAt: (Int) -> Boolean
    ): VideoSourceDeletionSummary {
        var deletedCount = 0
        var failedCount = 0

        repeat(sourceCount) { index ->
            if (deleteSourceAt(index)) {
                deletedCount += 1
            } else {
                failedCount += 1
            }
        }

        return VideoSourceDeletionSummary(
            deletedCount = deletedCount,
            failedCount = failedCount
        )
    }
}
