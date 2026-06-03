package com.example.wellfair

class OrchestrationSieve {

    /**
     * A native method that is implemented by the 'sieve' native library,
     * which is packaged with this application.
     */
    external fun processVisualHeraldry(imageData: ByteArray): String
    external fun processAudioPhonetics(audioData: ByteArray): String

    companion object {
        // Used to load the 'sieve' library on application startup.
        init {
            System.loadLibrary("sieve")
        }
    }
}
