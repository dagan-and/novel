package com.kys.videomanager.update

enum class ForceUpdateDecision {
    ALLOW,
    BLOCK
}

object ForceUpdatePolicy {
    fun resolve(currentVersionCode: Int, minSupportedVersionCode: Long): ForceUpdateDecision =
        if (currentVersionCode < minSupportedVersionCode) {
            ForceUpdateDecision.BLOCK
        } else {
            ForceUpdateDecision.ALLOW
        }
}
