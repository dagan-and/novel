package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class ProductCodeSearchNavigationPolicyTest {
    @Test fun `product-code search opens in external browser`() {
        val navigation = ProductCodeSearchNavigationPolicy.resolve()

        assertEquals(ProductCodeSearchNavigation.EXTERNAL_BROWSER, navigation.destination)
        assertEquals("https://avppomppu.com", navigation.url)
    }
}
