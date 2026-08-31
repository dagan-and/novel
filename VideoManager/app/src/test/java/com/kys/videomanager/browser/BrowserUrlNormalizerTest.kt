package com.kys.videomanager.browser

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class BrowserUrlNormalizerTest {

    @Test fun `bare domain gets https prefix`() {
        assertEquals("https://example.com", BrowserUrlNormalizer.normalize("example.com"))
    }

    @Test fun `already schemed https url passes through unchanged`() {
        assertEquals("https://example.com/path", BrowserUrlNormalizer.normalize("https://example.com/path"))
    }

    @Test fun `already schemed http url passes through unchanged`() {
        assertEquals("http://example.com", BrowserUrlNormalizer.normalize("http://example.com"))
    }

    @Test fun `surrounding whitespace is trimmed before normalizing`() {
        assertEquals("https://example.com", BrowserUrlNormalizer.normalize("  example.com  "))
    }

    @Test fun `blank input is rejected`() {
        assertNull(BrowserUrlNormalizer.normalize(""))
    }

    @Test fun `whitespace only input is rejected`() {
        assertNull(BrowserUrlNormalizer.normalize("   "))
    }

    @Test fun `non-http scheme is left unchanged`() {
        assertEquals("ftp://example.com", BrowserUrlNormalizer.normalize("ftp://example.com"))
    }
}
