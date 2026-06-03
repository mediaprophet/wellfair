package com.example.wellfair

/**
 * Represents the Verifiable Credential (VC) based identity demarcation.
 * This explicitly separates the user acting as a Natural Person (Free usage)
 * from the user acting as a Clinician/Agent of an Incorporated Entity (Licensed usage).
 */
enum class EntityType {
    NATURAL_PERSON,
    INCORPORATED_ENTITY
}

data class VerifiableCredential(
    val entityType: EntityType,
    val identifier: String,
    val isLicensed: Boolean
)

class FiduciaryOntology {
    
    /**
     * Asserts the cryptographic demarcation of the user's current session.
     */
    fun assertDemarcation(credential: VerifiableCredential): Boolean {
        return when (credential.entityType) {
            EntityType.NATURAL_PERSON -> {
                // Free usage, human-to-human data layer
                true
            }
            EntityType.INCORPORATED_ENTITY -> {
                // Subject to corporate licensing and audit
                credential.isLicensed
            }
        }
    }
}
