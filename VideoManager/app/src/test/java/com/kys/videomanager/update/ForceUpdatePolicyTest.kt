package com.kys.videomanager.update

import org.junit.Assert.assertEquals
import org.junit.Test

class ForceUpdatePolicyTest {

    @Test
    fun `current version equal to minimum allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 6, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `current version greater than minimum allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 7, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `current version less than minimum blocks`() {
        assertEquals(
            ForceUpdateDecision.BLOCK,
            ForceUpdatePolicy.resolve(currentVersionCode = 5, minSupportedVersionCode = 6L)
        )
    }

    @Test
    fun `default minimum of zero always allows`() {
        assertEquals(
            ForceUpdateDecision.ALLOW,
            ForceUpdatePolicy.resolve(currentVersionCode = 1, minSupportedVersionCode = 0L)
        )
    }
}
