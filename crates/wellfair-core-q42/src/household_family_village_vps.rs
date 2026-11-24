//! `household_family_village_vps`:
//!
//! Multi-Person Family, Household & Village Small-Business Personal VPS (`webizen-host`)
//! supporting Local Homestead Appliances (`:8080`), Online Cloud VPS Relays (`:4242`), and
//! Hybrid Paired Topologies.
//!
//! Models the enduring human pattern of the village family homestead:
//! - Multiple family members share a household VPS (`mercer-homestead.au`), each with an
//!   isolated 42 MiB `SlgArena` Prolog Sentinel cell, domain-separated Sanctuary Keep key,
//!   and personal QDP subdomain (`alex.mercer-homestead.au`, `elena.mercer-homestead.au`,
//!   `leo.mercer-homestead.au`, `maya.mercer-homestead.au`).
//! - Distinct adult craft, trade, or professional works coexist with strict compartment
//!   isolation:
//!   - **Father's Work (`forge.mercer-homestead.au`)**: Village Blacksmith, Custom Toolmaking &
//!     Precision CAD Fabrication Workshop (`poet.qap` + `cooperative-projects.qap`).
//!   - **Mother's Work (`apothecary.mercer-homestead.au`)**: Village Clinical Sanctuary,
//!     Autonomic Telehealth & Herbal/Pharmacokinetic Dispensary (`wellfair.qap`, AHPRA-gated).
//!   - **Shared Family Homestead Commons (`commons.mercer-homestead.au`)**: M-of-N co-stewarded
//!     household calendar, kitchen nutrition ledger, and solar microgrid.
//! - Dedicated guardian-stewarded services for children (`school.leo.mercer-homestead.au`,
//!   `school.maya.mercer-homestead.au`) interacting with schools (`melbourne-commons-school.edu.au`):
//!   - Enforces parental guardian quorum approval (`spc:GuardianshipArrangement` + `UNCRC`),
//!   - Anchors the child's learning claims (`cap:LearningClaim`) and authored `.hmc`/`.10d`
//!     portfolios inside the child's own vault on the family VPS for lifelong custody,
//!   - Blocks unconsented commercial trackers, AI scrapers, and unverified strangers fail-closed.
//!
//! Copyright (c) 2026 Timothy Charles Holborn. All rights reserved.
//! License: Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0).

use crate::domain_mail_and_sanctuary_importers::{q_hash_u64, NQuin48};
use serde::{Deserialize, Serialize};

/// Deployment topology for a Personal & Family `webizen-host` VPS.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PersonalVpsTopologyMode {
    /// Local household hardware appliance (`:8080` LAN / mesh homestead server).
    LocalHomesteadAppliance,
    /// Online cloud VPS (`:4242` public front-door relay + client-encrypted `.q42j` Shamir backup shards).
    OnlineCloudVpsRelay,
    /// Hybrid paired topology: local Sanctuary Keep hardware (`:8080`) paired with an online
    /// cloud VPS front-door (`:4242`) via Noise_XX + ML-KEM-1024 + QDNF tunnel.
    HybridPairedLocalAndCloudVps,
}

impl PersonalVpsTopologyMode {
    pub const fn label(self) -> &'static str {
        match self {
            Self::LocalHomesteadAppliance => {
                "Local Homestead Appliance (:8080 LAN/Mesh Sanctuary Keep)"
            }
            Self::OnlineCloudVpsRelay => {
                "Online Cloud VPS Front-Door (:4242 Encrypted .q42j Relay)"
            }
            Self::HybridPairedLocalAndCloudVps => {
                "Hybrid Paired Local Homestead (:8080) + Online Cloud VPS (:4242)"
            }
        }
    }
}

/// Role of a natural person seat on a Family & Village Personal VPS.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum HouseholdSeatRole {
    /// Adult parent/steward operating independent craft, trade, or fiduciary works (e.g. Father / Mother).
    AdultStewardAndCraftPrincipal {
        kinship_label: String,
        fiduciary_or_trade_title: String,
    },
    /// Child or adolescent dependent protected by `GuardianshipSemantics` (`UNCRC` + `spc:GuardianshipArrangement`).
    ChildOrAdolescentDependent {
        age_years: u8,
        guardian_dids: Vec<String>,
        enrolled_school_domain: Option<String>,
    },
    /// Supported elder or extended family member with optional co-signatory advocate.
    SupportedElderOrKin {
        kinship_label: String,
        advocate_guardian_did: Option<String>,
    },
}

/// An isolated natural-person seat on the Family & Village Personal VPS.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HouseholdVpsMemberSeat {
    pub seat_id: String,
    pub natural_person_did: String,
    pub display_name: String,
    pub personal_subdomain: String,
    pub role: HouseholdSeatRole,
    pub isolated_slg_arena_mib: u32,
    pub sanctuary_lane_fingerprint_hex: String,
}

/// A distinct craft, small-business shopfront, or professional practice hosted on the Family VPS
/// (e.g. Father's Blacksmith/Engineering Forge vs. Mother's Clinical Apothecary/Practice).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct VillageShopfrontOrCraftWork {
    pub work_id: String,
    pub title: String,
    pub craft_archetype: String,
    pub shopfront_subdomain: String,
    pub owner_principal_did: String,
    pub co_steward_dids: Vec<String>,
    pub treasury_account_id: String,
    pub hosted_qap_ids: Vec<String>,
    pub public_qcdn_catalog_enabled: bool,
    pub isolated_from_other_family_works: bool,
}

/// A guardian-authorized educational bridge connecting a child's seat on the Family VPS
/// (`school.<child>.<family-domain>`) with an external school (`<school-domain>`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChildSchoolFederationBridge {
    pub bridge_id: String,
    pub child_did: String,
    pub child_display_name: String,
    pub child_school_subdomain: String,
    pub school_institution_domain: String,
    pub school_institution_name: String,
    pub approving_guardian_dids: Vec<String>,
    pub required_guardian_quorum: usize,
    pub retain_learning_claims_in_family_vps: bool,
    pub block_unconsented_commercial_or_stranger_contact: bool,
    pub active: bool,
}

/// Outcome of evaluating an operation on a Family Craft Work or Child/School Bridge on the VPS.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FamilyVpsAccessOutcome {
    PermittedAdultCraftWork {
        work_id: String,
        shopfront_subdomain: String,
        receipt_quin: NQuin48,
    },
    PermittedGuardianApprovedSchoolExchange {
        bridge_id: String,
        child_school_subdomain: String,
        receipt_quin: NQuin48,
    },
    BlockedFailClosed {
        reason: String,
        receipt_quin: NQuin48,
    },
}

/// Complete Multi-Tenant Family, Household & Village Small-Business Personal VPS Node (`webizen-host`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FamilyVillagePersonalVps {
    pub vps_node_id: String,
    pub homestead_root_domain: String,
    pub topology: PersonalVpsTopologyMode,
    pub local_sanctuary_bind: String,
    pub online_relay_bind: Option<String>,
    pub seats: Vec<HouseholdVpsMemberSeat>,
    pub family_works: Vec<VillageShopfrontOrCraftWork>,
    pub school_bridges: Vec<ChildSchoolFederationBridge>,
}

impl FamilyVillagePersonalVps {
    /// Evaluates whether `caller_did` is permitted to administer or publish to a specific
    /// `VillageShopfrontOrCraftWork` on the Family VPS, enforcing strict compartment isolation
    /// between Father's works, Mother's works, and children's seats.
    pub fn authorize_family_craft_work_operation(
        &self,
        work_id: &str,
        caller_did: &str,
        now_unix: u64,
    ) -> FamilyVpsAccessOutcome {
        let make_quin = |code: u64| {
            NQuin48::new(
                q_hash_u64(work_id),
                q_hash_u64("vps:familyCraftWorkAccess"),
                code,
                q_hash_u64(caller_did),
                now_unix,
            )
        };

        let Some(work) = self.family_works.iter().find(|w| w.work_id == work_id) else {
            return FamilyVpsAccessOutcome::BlockedFailClosed {
                reason: format!(
                    "Work '{work_id}' not found on Family VPS '{}'",
                    self.homestead_root_domain
                ),
                receipt_quin: make_quin(0),
            };
        };

        if let Some(seat) = self.seats.iter().find(|s| s.natural_person_did == caller_did) {
            if matches!(seat.role, HouseholdSeatRole::ChildOrAdolescentDependent { .. }) {
                return FamilyVpsAccessOutcome::BlockedFailClosed {
                    reason: format!(
                        "Blocked: minor dependent seat '{}' cannot administer adult shopfront '{}'",
                        seat.display_name, work.shopfront_subdomain
                    ),
                    receipt_quin: make_quin(0),
                };
            }
        }

        if work.owner_principal_did == caller_did
            || work.co_steward_dids.iter().any(|d| d == caller_did)
        {
            FamilyVpsAccessOutcome::PermittedAdultCraftWork {
                work_id: work.work_id.clone(),
                shopfront_subdomain: work.shopfront_subdomain.clone(),
                receipt_quin: make_quin(1),
            }
        } else {
            FamilyVpsAccessOutcome::BlockedFailClosed {
                reason: format!(
                    "Compartment Isolation: '{}' is owned by '{}' and isolated from caller '{}'",
                    work.shopfront_subdomain, work.owner_principal_did, caller_did
                ),
                receipt_quin: make_quin(0),
            }
        }
    }

    /// Evaluates an educational interaction between an external school (`caller_school_domain`)
    /// and a child's seat (`child_did`) on the Family VPS.
    pub fn evaluate_child_school_interaction(
        &self,
        child_did: &str,
        caller_school_domain: &str,
        is_commercial_tracker_or_unverified_stranger: bool,
        now_unix: u64,
    ) -> FamilyVpsAccessOutcome {
        let make_quin = |code: u64| {
            NQuin48::new(
                q_hash_u64(child_did),
                q_hash_u64("vps:childSchoolFederationGate"),
                code,
                q_hash_u64(caller_school_domain),
                now_unix,
            )
        };

        if is_commercial_tracker_or_unverified_stranger {
            return FamilyVpsAccessOutcome::BlockedFailClosed {
                reason: "Child Protection Gate: blocked unconsented commercial tracker or unverified stranger contact with minor seat".to_string(),
                receipt_quin: make_quin(0),
            };
        }

        let Some(bridge) = self.school_bridges.iter().find(|b| {
            b.child_did == child_did
                && b.school_institution_domain
                    .eq_ignore_ascii_case(caller_school_domain)
        }) else {
            return FamilyVpsAccessOutcome::BlockedFailClosed {
                reason: format!(
                    "Child Protection Gate: domain '{caller_school_domain}' has no guardian-approved school federation bridge for '{child_did}'"
                ),
                receipt_quin: make_quin(0),
            };
        };

        if !bridge.active
            || bridge.approving_guardian_dids.len() < bridge.required_guardian_quorum
        {
            return FamilyVpsAccessOutcome::BlockedFailClosed {
                reason: format!(
                    "Child Protection Gate: school bridge '{}' lacks required parental guardian quorum ({}/{})",
                    bridge.bridge_id,
                    bridge.approving_guardian_dids.len(),
                    bridge.required_guardian_quorum
                ),
                receipt_quin: make_quin(0),
            };
        }

        FamilyVpsAccessOutcome::PermittedGuardianApprovedSchoolExchange {
            bridge_id: bridge.bridge_id.clone(),
            child_school_subdomain: bridge.child_school_subdomain.clone(),
            receipt_quin: make_quin(1),
        }
    }
}

/// Builds the canonical seeded Family & Village Small-Business Personal VPS (`mercer-homestead.au`).
pub fn build_seeded_family_village_personal_vps() -> FamilyVillagePersonalVps {
    let alex_did = "did:webizen:person:alex-mercer";
    let elena_did = "did:webizen:person:dr-elena-rostova";
    let leo_did = "did:webizen:person:leo-mercer";
    let maya_did = "did:webizen:person:maya-mercer";

    let seats = vec![
        HouseholdVpsMemberSeat {
            seat_id: "SEAT-FATHER-ALEX".to_string(),
            natural_person_did: alex_did.to_string(),
            display_name: "Alex Mercer (Father · Master Blacksmith & Precision CAD Fabricator)".to_string(),
            personal_subdomain: "alex.mercer-homestead.au".to_string(),
            role: HouseholdSeatRole::AdultStewardAndCraftPrincipal {
                kinship_label: "Father & Co-Steward Guardian".to_string(),
                fiduciary_or_trade_title: "Master Blacksmith, Toolmaker & Systems Engineer".to_string(),
            },
            isolated_slg_arena_mib: 42,
            sanctuary_lane_fingerprint_hex: "pbkdf2_hkdf_lane_alex_99a1e4c2".to_string(),
        },
        HouseholdVpsMemberSeat {
            seat_id: "SEAT-MOTHER-ELENA".to_string(),
            natural_person_did: elena_did.to_string(),
            display_name: "Dr. Elena Rostova-Mercer (Mother · Clinical Psychiatrist & Apothecary)".to_string(),
            personal_subdomain: "elena.mercer-homestead.au".to_string(),
            role: HouseholdSeatRole::AdultStewardAndCraftPrincipal {
                kinship_label: "Mother & Co-Steward Guardian".to_string(),
                fiduciary_or_trade_title: "Specialist Medical Practitioner (AHPRA MED0001849201)".to_string(),
            },
            isolated_slg_arena_mib: 42,
            sanctuary_lane_fingerprint_hex: "pbkdf2_hkdf_lane_elena_88b2f5d3".to_string(),
        },
        HouseholdVpsMemberSeat {
            seat_id: "SEAT-CHILD-LEO".to_string(),
            natural_person_did: leo_did.to_string(),
            display_name: "Leo Mercer (Child · Age 11 · Year 6 Student)".to_string(),
            personal_subdomain: "leo.mercer-homestead.au".to_string(),
            role: HouseholdSeatRole::ChildOrAdolescentDependent {
                age_years: 11,
                guardian_dids: vec![alex_did.to_string(), elena_did.to_string()],
                enrolled_school_domain: Some("melbourne-commons-school.edu.au".to_string()),
            },
            isolated_slg_arena_mib: 42,
            sanctuary_lane_fingerprint_hex: "pbkdf2_hkdf_lane_leo_77c3a6e4".to_string(),
        },
        HouseholdVpsMemberSeat {
            seat_id: "SEAT-CHILD-MAYA".to_string(),
            natural_person_did: maya_did.to_string(),
            display_name: "Maya Mercer (Adolescent · Age 15 · Year 10 STEM & Music Apprentice)".to_string(),
            personal_subdomain: "maya.mercer-homestead.au".to_string(),
            role: HouseholdSeatRole::ChildOrAdolescentDependent {
                age_years: 15,
                guardian_dids: vec![alex_did.to_string(), elena_did.to_string()],
                enrolled_school_domain: Some("melbourne-commons-school.edu.au".to_string()),
            },
            isolated_slg_arena_mib: 42,
            sanctuary_lane_fingerprint_hex: "pbkdf2_hkdf_lane_maya_66d4b7f5".to_string(),
        },
    ];

    let family_works = vec![
        VillageShopfrontOrCraftWork {
            work_id: "WORK-FATHER-FORGE".to_string(),
            title: "Mercer Village Forge & Precision CAD Fabrication Workshop".to_string(),
            craft_archetype: "Village Blacksmith, Custom Joinery & Precision Engineering Shopfront".to_string(),
            shopfront_subdomain: "forge.mercer-homestead.au".to_string(),
            owner_principal_did: alex_did.to_string(),
            co_steward_dids: vec![],
            treasury_account_id: "acct-father-forge-trade".to_string(),
            hosted_qap_ids: vec!["poet".to_string(), "cooperative-projects".to_string()],
            public_qcdn_catalog_enabled: true,
            isolated_from_other_family_works: true,
        },
        VillageShopfrontOrCraftWork {
            work_id: "WORK-MOTHER-APOTHECARY".to_string(),
            title: "Rostova Village Clinical Practice & Autonomic Sanctuary Dispensary".to_string(),
            craft_archetype: "Family Doctor, Autonomic Telehealth & Herbal/Pharmacokinetic Apothecary".to_string(),
            shopfront_subdomain: "apothecary.mercer-homestead.au".to_string(),
            owner_principal_did: elena_did.to_string(),
            co_steward_dids: vec![],
            treasury_account_id: "acct-mother-clinical-practice".to_string(),
            hosted_qap_ids: vec!["wellfair".to_string()],
            public_qcdn_catalog_enabled: true,
            isolated_from_other_family_works: true,
        },
        VillageShopfrontOrCraftWork {
            work_id: "WORK-FAMILY-COMMONS".to_string(),
            title: "Mercer Household Commons, Kitchen Ledger & Solar Microgrid".to_string(),
            craft_archetype: "Shared Family Homestead Calendar, Nutrition & Mutual Stewardship".to_string(),
            shopfront_subdomain: "commons.mercer-homestead.au".to_string(),
            owner_principal_did: alex_did.to_string(),
            co_steward_dids: vec![elena_did.to_string()],
            treasury_account_id: "acct-family-household-commons".to_string(),
            hosted_qap_ids: vec!["wellfair".to_string(), "cooperative-projects".to_string()],
            public_qcdn_catalog_enabled: false,
            isolated_from_other_family_works: true,
        },
    ];

    let school_bridges = vec![
        ChildSchoolFederationBridge {
            bridge_id: "BRIDGE-SCHOOL-LEO-01".to_string(),
            child_did: leo_did.to_string(),
            child_display_name: "Leo Mercer (Age 11 · Year 6)".to_string(),
            child_school_subdomain: "school.leo.mercer-homestead.au".to_string(),
            school_institution_domain: "melbourne-commons-school.edu.au".to_string(),
            school_institution_name: "Melbourne Cooperative & Civic Grammar School".to_string(),
            approving_guardian_dids: vec![alex_did.to_string(), elena_did.to_string()],
            required_guardian_quorum: 1,
            retain_learning_claims_in_family_vps: true,
            block_unconsented_commercial_or_stranger_contact: true,
            active: true,
        },
        ChildSchoolFederationBridge {
            bridge_id: "BRIDGE-SCHOOL-MAYA-02".to_string(),
            child_did: maya_did.to_string(),
            child_display_name: "Maya Mercer (Age 15 · Year 10)".to_string(),
            child_school_subdomain: "school.maya.mercer-homestead.au".to_string(),
            school_institution_domain: "melbourne-commons-school.edu.au".to_string(),
            school_institution_name: "Melbourne Cooperative & Civic Grammar School".to_string(),
            approving_guardian_dids: vec![alex_did.to_string(), elena_did.to_string()],
            required_guardian_quorum: 1,
            retain_learning_claims_in_family_vps: true,
            block_unconsented_commercial_or_stranger_contact: true,
            active: true,
        },
    ];

    FamilyVillagePersonalVps {
        vps_node_id: "VPS-MERCER-HOMESTEAD-AU-01".to_string(),
        homestead_root_domain: "mercer-homestead.au".to_string(),
        topology: PersonalVpsTopologyMode::HybridPairedLocalAndCloudVps,
        local_sanctuary_bind: "192.168.1.42:8080".to_string(),
        online_relay_bind: Some("vps.mercer-homestead.au:4242".to_string()),
        seats,
        family_works,
        school_bridges,
    }
}

// ============================================================================
// MULTI-DEVICE STORE-AND-FORWARD MESH (PHONE ELEVATION + INTERMITTENT LAPTOP +
// MAC MINI HOME SERVER / VPS PERSISTENCE) & NOMINATED VPS ABN/TRADE INSTALLER
// ============================================================================

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeviceEndpointRole {
    PhonePocketCosignerAndElevator,
    IntermittentDesktopOrLaptopWorkstation,
    DedicatedHomeServerAppliance,
    OnlineCloudVpsPersistenceRelay,
}

impl DeviceEndpointRole {
    pub const fn label(self) -> &'static str {
        match self {
            Self::PhonePocketCosignerAndElevator => {
                "Phone Install (Hardware Pocket Co-Signer & Permission Elevator)"
            }
            Self::IntermittentDesktopOrLaptopWorkstation => {
                "Desktop / Laptop Workstation (Intermittent Availability)"
            }
            Self::DedicatedHomeServerAppliance => {
                "Dedicated Home Server (e.g. Mac Mini / Local Persistence Appliance :8080)"
            }
            Self::OnlineCloudVpsPersistenceRelay => {
                "Online Cloud VPS (Always-On Encrypted Persistence & Q-CDN Relay :4242)"
            }
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeviceAvailabilityState {
    OnlineReady,
    OnlineLowPowerCosignerOnly,
    OfflineOrSleeping,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct UserDeviceEndpoint {
    pub device_id: String,
    pub owner_did: String,
    pub display_name: String,
    pub role: DeviceEndpointRole,
    pub availability: DeviceAvailabilityState,
    pub is_designated_persistence_layer: bool,
    pub wireguard_or_qdnf_endpoint: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DispatchedPayloadKind {
    QdpRelationshipScopedMail,
    ChatGraphDelegatedTurnOrMessage,
    CrossQapLibraryArtifactShare,
    CooperativeProjectClaimOrSettlement,
    QcdnContentDistributionBundle,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum SpoolDeliveryState {
    QueuedInSenderOutboundRetrySpool,
    SpooledAtRecipientPersistenceLayerAwaitingWorkstation,
    ElevatedByPhoneCosignerAwaitingWorkstationHydration,
    DeliveredAndHydratedOnWorkstation,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct StoreAndForwardEnvelope {
    pub envelope_id: String,
    pub sender_did: String,
    pub recipient_did: String,
    pub payload_kind: DispatchedPayloadKind,
    pub summary_subject: String,
    pub encrypted_payload_digest_hex: String,
    pub requires_phone_permission_elevation: bool,
    pub phone_elevation_signature_hex: Option<String>,
    pub target_persistence_node_id: Option<String>,
    pub delivery_state: SpoolDeliveryState,
    pub lamport_clock: u64,
    pub receipt_quin: NQuin48,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MultiDevicePersistenceMesh {
    pub owner_did: String,
    pub devices: Vec<UserDeviceEndpoint>,
    pub spooled_envelopes: Vec<StoreAndForwardEnvelope>,
    pub next_lamport: u64,
}

impl MultiDevicePersistenceMesh {
    #[allow(clippy::too_many_arguments)]
    pub fn dispatch_respecting_availability(
        &mut self,
        envelope_id: impl Into<String>,
        sender_did: impl Into<String>,
        payload_kind: DispatchedPayloadKind,
        summary_subject: impl Into<String>,
        encrypted_payload_digest_hex: impl Into<String>,
        requires_phone_permission_elevation: bool,
        now_unix: u64,
    ) -> StoreAndForwardEnvelope {
        self.next_lamport += 1;
        let env_id = envelope_id.into();
        let sender = sender_did.into();

        let workstation_online = self.devices.iter().any(|d| {
            d.role == DeviceEndpointRole::IntermittentDesktopOrLaptopWorkstation
                && d.availability == DeviceAvailabilityState::OnlineReady
        });

        let active_persistence_node = self
            .devices
            .iter()
            .find(|d| {
                d.is_designated_persistence_layer
                    && d.availability != DeviceAvailabilityState::OfflineOrSleeping
            })
            .map(|d| d.device_id.clone());

        let delivery_state = if workstation_online && !requires_phone_permission_elevation {
            SpoolDeliveryState::DeliveredAndHydratedOnWorkstation
        } else if active_persistence_node.is_some() {
            SpoolDeliveryState::SpooledAtRecipientPersistenceLayerAwaitingWorkstation
        } else {
            SpoolDeliveryState::QueuedInSenderOutboundRetrySpool
        };

        let quin = NQuin48::new(
            q_hash_u64(&env_id),
            q_hash_u64("vps:storeAndForwardDispatch"),
            q_hash_u64(&self.owner_did),
            q_hash_u64(&sender),
            now_unix,
        );

        let env = StoreAndForwardEnvelope {
            envelope_id: env_id,
            sender_did: sender,
            recipient_did: self.owner_did.clone(),
            payload_kind,
            summary_subject: summary_subject.into(),
            encrypted_payload_digest_hex: encrypted_payload_digest_hex.into(),
            requires_phone_permission_elevation,
            phone_elevation_signature_hex: None,
            target_persistence_node_id: active_persistence_node,
            delivery_state,
            lamport_clock: self.next_lamport,
            receipt_quin: quin,
        };
        self.spooled_envelopes.push(env.clone());
        env
    }

    pub fn elevate_permission_on_phone(
        &mut self,
        envelope_id: &str,
        phone_cosign_hex: impl Into<String>,
    ) -> Result<SpoolDeliveryState, String> {
        let phone_online = self.devices.iter().any(|d| {
            d.role == DeviceEndpointRole::PhonePocketCosignerAndElevator
                && d.availability != DeviceAvailabilityState::OfflineOrSleeping
        });
        if !phone_online {
            return Err("Phone Pocket Co-Signer is currently offline".to_string());
        }
        let env = self
            .spooled_envelopes
            .iter_mut()
            .find(|e| e.envelope_id == envelope_id)
            .ok_or_else(|| format!("Envelope '{envelope_id}' not found in persistence spool"))?;
        env.phone_elevation_signature_hex = Some(phone_cosign_hex.into());
        if env.delivery_state != SpoolDeliveryState::DeliveredAndHydratedOnWorkstation {
            env.delivery_state =
                SpoolDeliveryState::ElevatedByPhoneCosignerAwaitingWorkstationHydration;
        }
        Ok(env.delivery_state)
    }

    pub fn wake_workstation_and_drain_spool(&mut self) -> usize {
        for d in &mut self.devices {
            if d.role == DeviceEndpointRole::IntermittentDesktopOrLaptopWorkstation {
                d.availability = DeviceAvailabilityState::OnlineReady;
            }
        }
        let mut hydrated_count = 0usize;
        for env in &mut self.spooled_envelopes {
            if env.delivery_state != SpoolDeliveryState::DeliveredAndHydratedOnWorkstation
                && (!env.requires_phone_permission_elevation
                    || env.phone_elevation_signature_hex.is_some())
            {
                env.delivery_state = SpoolDeliveryState::DeliveredAndHydratedOnWorkstation;
                hydrated_count += 1;
            }
        }
        hydrated_count
    }
}

pub fn validate_australian_abn_mod89(raw_abn: &str) -> Result<String, String> {
    let digits: Vec<u32> = raw_abn
        .chars()
        .filter(|c| !c.is_whitespace() && *c != '-')
        .map(|c| {
            c.to_digit(10)
                .ok_or_else(|| format!("Invalid non-digit character '{c}' in ABN '{raw_abn}'"))
        })
        .collect::<Result<Vec<u32>, String>>()?;

    if digits.len() != 11 {
        return Err(format!(
            "Australian ABN must have exactly 11 digits (got {} in '{raw_abn}')",
            digits.len()
        ));
    }
    if digits[0] == 0 {
        return Err("Australian ABN cannot start with 0".to_string());
    }

    const WEIGHTS: [u32; 11] = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
    let mut sum = (digits[0] - 1) * WEIGHTS[0];
    for i in 1..11 {
        sum += digits[i] * WEIGHTS[i];
    }

    if sum % 89 != 0 {
        return Err(format!(
            "ABN '{raw_abn}' failed ATO Modulus-89 checksum (sum={sum}, sum % 89 = {})",
            sum % 89
        ));
    }

    Ok(format!(
        "{}{} {}{}{} {}{}{} {}{}{}",
        digits[0],
        digits[1],
        digits[2],
        digits[3],
        digits[4],
        digits[5],
        digits[6],
        digits[7],
        digits[8],
        digits[9],
        digits[10]
    ))
}

pub const AU_STANDARD_GST_THRESHOLD_CENTS: u64 = 7_500_000;
pub const AU_NON_PROFIT_GST_THRESHOLD_CENTS: u64 = 15_000_000;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum VpsTradeAndAbnCharacterisation {
    CostRecoveryAndMicroTradeBelowAbnThreshold {
        statement_by_supplier_reason: String,
        monthly_hosting_and_bandwidth_cost_cents: u64,
    },
    RegisteredAustralianTradeWithAbn {
        abn_formatted: String,
        entity_trading_name: String,
        projected_annual_turnover_cents: u64,
        gst_registered_10_percent: bool,
        monthly_hosting_and_bandwidth_cost_cents: u64,
    },
    CooperativeCommonsWithAbn {
        abn_formatted: String,
        cooperative_name: String,
        projected_annual_turnover_cents: u64,
        gst_registered_10_percent: bool,
        monthly_hosting_and_bandwidth_cost_cents: u64,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct VpsProviderNominationInfo {
    pub provider_name: String,
    pub region_and_jurisdiction_iso: String,
    pub public_ipv4: String,
    pub public_ipv6: Option<String>,
    pub ssh_port: u16,
    pub bootstrap_auth_fingerprint: String,
    pub primary_qdp_domain: String,
    pub steward_natural_person_did: String,
    pub monthly_bandwidth_quota_gib: u64,
    pub storage_quota_gib: u64,
    pub raw_australian_abn: Option<String>,
    pub trading_or_homestead_name: String,
    pub is_non_profit_cooperative: bool,
    pub projected_annual_turnover_cents: u64,
    pub monthly_provider_invoice_cost_cents: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct InstigatedVpsInstallationPlan {
    pub installation_id: String,
    pub provider_name: String,
    pub target_host_endpoint: String,
    pub primary_qdp_domain: String,
    pub trade_characterisation: VpsTradeAndAbnCharacterisation,
    pub auto_gst_escrow_enabled: bool,
    pub qcdn_cost_recovery_pool_target_cents: u64,
    pub generated_qdp_dns_txt_record: String,
    pub generated_bootstrap_command: String,
    pub receipt_quin: NQuin48,
}

pub fn instigate_nominated_vps_installation(
    info: &VpsProviderNominationInfo,
    now_unix: u64,
) -> Result<InstigatedVpsInstallationPlan, String> {
    if info.public_ipv4.trim().is_empty() || info.primary_qdp_domain.trim().is_empty() {
        return Err("VPS nomination requires a non-empty public IPv4/IPv6 address and primary QDP domain".to_string());
    }

    let (trade_characterisation, auto_gst_escrow_enabled, abn_opt) =
        if let Some(ref raw_abn) = info.raw_australian_abn {
            let formatted_abn = validate_australian_abn_mod89(raw_abn)?;
            if info.is_non_profit_cooperative {
                let gst = info.projected_annual_turnover_cents >= AU_NON_PROFIT_GST_THRESHOLD_CENTS;
                (
                    VpsTradeAndAbnCharacterisation::CooperativeCommonsWithAbn {
                        abn_formatted: formatted_abn.clone(),
                        cooperative_name: info.trading_or_homestead_name.clone(),
                        projected_annual_turnover_cents: info.projected_annual_turnover_cents,
                        gst_registered_10_percent: gst,
                        monthly_hosting_and_bandwidth_cost_cents: info.monthly_provider_invoice_cost_cents,
                    },
                    gst,
                    Some(formatted_abn),
                )
            } else {
                let gst = info.projected_annual_turnover_cents >= AU_STANDARD_GST_THRESHOLD_CENTS;
                (
                    VpsTradeAndAbnCharacterisation::RegisteredAustralianTradeWithAbn {
                        abn_formatted: formatted_abn.clone(),
                        entity_trading_name: info.trading_or_homestead_name.clone(),
                        projected_annual_turnover_cents: info.projected_annual_turnover_cents,
                        gst_registered_10_percent: gst,
                        monthly_hosting_and_bandwidth_cost_cents: info.monthly_provider_invoice_cost_cents,
                    },
                    gst,
                    Some(formatted_abn),
                )
            }
        } else {
            if info.projected_annual_turnover_cents >= AU_STANDARD_GST_THRESHOLD_CENTS {
                return Err(format!(
                    "Projected annual turnover ({} AUD cents) meets or exceeds the $75,000 AUD GST threshold; a valid 11-digit Australian ABN is required",
                    info.projected_annual_turnover_cents
                ));
            }
            (
                VpsTradeAndAbnCharacterisation::CostRecoveryAndMicroTradeBelowAbnThreshold {
                    statement_by_supplier_reason:
                        "ATO Statement by a Supplier: Infrastructure & Q-CDN content distribution cost-recovery below $75,000 AUD threshold"
                            .to_string(),
                    monthly_hosting_and_bandwidth_cost_cents: info.monthly_provider_invoice_cost_cents,
                },
                false,
                None,
            )
        };

    let qcdn_cost_recovery_pool_target_cents = info.monthly_provider_invoice_cost_cents.saturating_mul(12);
    let abn_clause = abn_opt
        .as_ref()
        .map(|a| format!("; qdp:abn \"{}\"", a))
        .unwrap_or_else(|| "; qdp:costRecovery \"ATO-Statement-By-Supplier\"".to_string());
    let generated_qdp_dns_txt_record = format!(
        "_qdp.{} IN TXT \"v=QDP1; qdp:signer <{}>; qdp:ipv4 \"{}\"{}; qdp:costRecoveryTargetCents \"{}\"; qdp:gstEscrow \"{}\"",
        info.primary_qdp_domain,
        info.steward_natural_person_did,
        info.public_ipv4,
        abn_clause,
        qcdn_cost_recovery_pool_target_cents,
        auto_gst_escrow_enabled
    );
    let generated_bootstrap_command = format!(
        "ssh -p {} root@{} \"WEBIZEN_DOMAIN='{}' WEBIZEN_STEWARD_DID='{}' WEBIZEN_COST_RECOVERY_CENTS='{}' WEBIZEN_GST_ESCROW='{}' bash -s\" < /var/lib/webizen-host/deploy/install-vps.sh",
        info.ssh_port,
        info.public_ipv4,
        info.primary_qdp_domain,
        info.steward_natural_person_did,
        qcdn_cost_recovery_pool_target_cents,
        auto_gst_escrow_enabled
    );

    let installation_id = format!("VPS-INST-{}", info.primary_qdp_domain.replace('.', "-"));
    let receipt_quin = NQuin48::new(
        q_hash_u64(&installation_id),
        q_hash_u64("vps:instigatedNominatedVpsInstallation"),
        q_hash_u64(&info.primary_qdp_domain),
        q_hash_u64(&info.steward_natural_person_did),
        now_unix,
    );

    Ok(InstigatedVpsInstallationPlan {
        installation_id,
        provider_name: info.provider_name.clone(),
        target_host_endpoint: format!("{}:{}", info.public_ipv4, info.ssh_port),
        primary_qdp_domain: info.primary_qdp_domain.clone(),
        trade_characterisation,
        auto_gst_escrow_enabled,
        qcdn_cost_recovery_pool_target_cents,
        generated_qdp_dns_txt_record,
        generated_bootstrap_command,
        receipt_quin,
    })
}

pub fn build_seeded_multi_device_persistence_mesh() -> MultiDevicePersistenceMesh {
    let owner_did = "did:webizen:person:alex-mercer";
    MultiDevicePersistenceMesh {
        owner_did: owner_did.to_string(),
        devices: vec![
            UserDeviceEndpoint {
                device_id: "DEV-PHONE-POCKET-COSIGNER".to_string(),
                owner_did: owner_did.to_string(),
                display_name: "Alex's Pixel 9 Pro (AVF Pocket Co-Signer & Permission Elevator)".to_string(),
                role: DeviceEndpointRole::PhonePocketCosignerAndElevator,
                availability: DeviceAvailabilityState::OnlineLowPowerCosignerOnly,
                is_designated_persistence_layer: false,
                wireguard_or_qdnf_endpoint: "10.42.0.2:51820".to_string(),
            },
            UserDeviceEndpoint {
                device_id: "DEV-LAPTOP-WORKSTATION".to_string(),
                owner_did: owner_did.to_string(),
                display_name: "Alex's Laptop Workstation (Poet / WellFair / Coop — Currently Asleep/Offline)".to_string(),
                role: DeviceEndpointRole::IntermittentDesktopOrLaptopWorkstation,
                availability: DeviceAvailabilityState::OfflineOrSleeping,
                is_designated_persistence_layer: false,
                wireguard_or_qdnf_endpoint: "10.42.0.3:51820".to_string(),
            },
            UserDeviceEndpoint {
                device_id: "DEV-MAC-MINI-HOME-SERVER".to_string(),
                owner_did: owner_did.to_string(),
                display_name: "Mercer Homestead Mac Mini M4 Home Server (Local Always-On Persistence :8080)".to_string(),
                role: DeviceEndpointRole::DedicatedHomeServerAppliance,
                availability: DeviceAvailabilityState::OnlineReady,
                is_designated_persistence_layer: true,
                wireguard_or_qdnf_endpoint: "192.168.1.42:8080".to_string(),
            },
            UserDeviceEndpoint {
                device_id: "DEV-BINARYLANE-CLOUD-VPS".to_string(),
                owner_did: owner_did.to_string(),
                display_name: "BinaryLane Melbourne Cloud VPS (Encrypted Store-and-Forward & Q-CDN Relay :4242)".to_string(),
                role: DeviceEndpointRole::OnlineCloudVpsPersistenceRelay,
                availability: DeviceAvailabilityState::OnlineReady,
                is_designated_persistence_layer: true,
                wireguard_or_qdnf_endpoint: "203.0.113.42:4242".to_string(),
            },
        ],
        spooled_envelopes: Vec::new(),
        next_lamport: 100,
    }
}

pub fn build_seeded_australian_abn_vps_nomination() -> VpsProviderNominationInfo {
    VpsProviderNominationInfo {
        provider_name: "BinaryLane Melbourne".to_string(),
        region_and_jurisdiction_iso: "AU-VIC".to_string(),
        public_ipv4: "203.0.113.42".to_string(),
        public_ipv6: Some("2001:db8:42::1".to_string()),
        ssh_port: 22,
        bootstrap_auth_fingerprint: "SHA256:mercer-homestead-ed25519-key".to_string(),
        primary_qdp_domain: "forge.mercer-homestead.au".to_string(),
        steward_natural_person_did: "did:webizen:person:alex-mercer".to_string(),
        monthly_bandwidth_quota_gib: 2000,
        storage_quota_gib: 160,
        raw_australian_abn: Some("51 824 753 556".to_string()),
        trading_or_homestead_name: "Mercer Village Forge & Precision CAD Fabrication".to_string(),
        is_non_profit_cooperative: false,
        projected_annual_turnover_cents: 9_500_000,
        monthly_provider_invoice_cost_cents: 4_500,
    }
}

// ============================================================================
// 4. WSL2 LINUX KERNEL COMPATIBILITY BRIDGE & WINDOWS-TO-WEBIZEN PRIMARY OS PORTABILITY CAPSULE
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Wsl2AndPrimaryOsSubstrateMode {
    WindowsHostWithWsl2KernelBridgeOffload,
    InsideWsl2DebianTrixieGuest,
    WindowsNativeUserSpaceOnly,
    WebizenPrimaryOsDebianTrixieAppliance,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Wsl2LinuxKernelBridgeProfile {
    pub substrate_mode: Wsl2AndPrimaryOsSubstrateMode,
    pub wsl2_distro_name: String,
    pub kernel_release: String,
    pub ebpf_socket_quota_enforcement_active: bool,
    pub nftables_deontic_split_horizon_active: bool,
    pub ext4_posix_mmap_vault_active: bool,
    pub systemd_hostd_parity_active: bool,
    pub wsl2_launch_command: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WindowsToWebizenPrimaryOsMigrationCapsule {
    pub capsule_id: String,
    pub principal_did: String,
    pub source_substrate: Wsl2AndPrimaryOsSubstrateMode,
    pub target_primary_os_sku: String,
    pub preserved_q42_volumes_count: usize,
    pub preserved_qap_packages_count: usize,
    pub preserved_qar_evidentiary_archives_count: usize,
    pub evidentiary_timestamps_preserved_across_os_wipe: bool,
    pub shamir_q42j_journal_digest_hex: String,
    pub sanctuary_vault_v2_cbor_digest_hex: String,
    pub phone_pocket_cosigner_reanchor_sig_hex: String,
    pub debian_appliance_install_command: String,
    pub receipt_quin: NQuin48,
}

pub fn build_wsl2_linux_kernel_bridge_profile(
    wsl2_available_on_host: bool,
) -> Wsl2LinuxKernelBridgeProfile {
    let substrate_mode = if wsl2_available_on_host {
        Wsl2AndPrimaryOsSubstrateMode::WindowsHostWithWsl2KernelBridgeOffload
    } else {
        Wsl2AndPrimaryOsSubstrateMode::WindowsNativeUserSpaceOnly
    };
    Wsl2LinuxKernelBridgeProfile {
        substrate_mode,
        wsl2_distro_name: "Debian-13-Trixie-Webizen-Bridge".to_string(),
        kernel_release: "6.6.87.2-microsoft-standard-WSL2".to_string(),
        ebpf_socket_quota_enforcement_active: wsl2_available_on_host,
        nftables_deontic_split_horizon_active: wsl2_available_on_host,
        ext4_posix_mmap_vault_active: wsl2_available_on_host,
        systemd_hostd_parity_active: wsl2_available_on_host,
        wsl2_launch_command:
            "wsl.exe -d Debian-13-Trixie-Webizen-Bridge -u root -- systemctl enable --now webizen-hostd.service && nft -f /etc/webizen-host/nftables-qpolicy.conf"
                .to_string(),
    }
}

pub fn seal_windows_to_webizen_primary_os_migration_capsule(
    principal_did: &str,
    source_substrate: Wsl2AndPrimaryOsSubstrateMode,
    preserved_q42_volumes_count: usize,
    preserved_qap_packages_count: usize,
    preserved_qar_evidentiary_archives_count: usize,
    phone_pocket_cosigner_reanchor_sig_hex: &str,
    now_unix: u64,
) -> Result<WindowsToWebizenPrimaryOsMigrationCapsule, String> {
    if phone_pocket_cosigner_reanchor_sig_hex.trim().is_empty() {
        return Err(
            "Primary OS Migration requires a non-empty Phone Pocket Co-Signer signature to re-anchor Sanctuary keys on the new Linux Anvil .np64 hardware profile"
                .to_string(),
        );
    }
    if preserved_q42_volumes_count == 0 || preserved_qap_packages_count == 0 {
        return Err("Migration capsule must include at least one .q42 semantic volume and one .qap application package".to_string());
    }
    let capsule_id = format!(
        "MIGRATE-PRIMARY-OS-{}",
        principal_did.replace([':', '.'], "-")
    );
    let receipt_quin = NQuin48::new(
        q_hash_u64(&capsule_id),
        q_hash_u64("os:windowsToWebizenPrimaryOsCutover"),
        q_hash_u64(principal_did),
        q_hash_u64(phone_pocket_cosigner_reanchor_sig_hex),
        now_unix,
    );
    Ok(WindowsToWebizenPrimaryOsMigrationCapsule {
        capsule_id,
        principal_did: principal_did.to_string(),
        source_substrate,
        target_primary_os_sku:
            "SKU-B: Debian 13 (trixie) + webizen-desktop-appliance_0.1.0_amd64.deb + webizen-hostd_0.1.0_amd64.deb"
                .to_string(),
        preserved_q42_volumes_count,
        preserved_qap_packages_count,
        preserved_qar_evidentiary_archives_count,
        evidentiary_timestamps_preserved_across_os_wipe: true,
        shamir_q42j_journal_digest_hex:
            "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08".to_string(),
        sanctuary_vault_v2_cbor_digest_hex:
            "sha256:4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a".to_string(),
        phone_pocket_cosigner_reanchor_sig_hex: phone_pocket_cosigner_reanchor_sig_hex.to_string(),
        debian_appliance_install_command:
            "sudo dpkg -i /media/webizen-migration/webizen-hostd_0.1.0_amd64.deb /media/webizen-migration/webizen-desktop-appliance_0.1.0_amd64.deb && webizen-os-shell portability restore-primary-os-capsule --capsule /media/webizen-migration/primary-os-capsule.qar"
                .to_string(),
        receipt_quin,
    })
}

// ============================================================================
// 5. PROGRESSIVE DESKTOP & MOBILE ONBOARDING CONFIDENCE LADDER &
//    MULTI-ACCOUNT / MULTI-USER SHARED-MACHINE SEAT ASSIGNMENTS
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OnboardingConfidenceTier {
    Tier0UnverifiedGuest,
    Tier1LocalApparatusBound,
    Tier2DesktopAndMobilePaired,
    Tier3HighAssuranceMultiFactorPrincipal,
    RejectedDefinitiveCollapse,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OnboardingIdentifierEvidence {
    pub identifier_uri: String,
    pub plane: String,
    pub modality_role: String,
    pub crypto_scheme: String,
    pub attested: bool,
    pub confidence_permille: u16,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SharedMachineAccountAssignmentKind {
    PrimaryPersonalSanctuaryAccount { household_role: String },
    ProfessionalFiduciaryPersonaAccount {
        sector: String,
        qualification_credential_id: String,
        jurisdiction_iso: String,
    },
    CoStewardOrHousematePeerAccount { relationship_label: String },
    ChildOrSupportedDependentAccount {
        agency_stage: String,
        guardian_dids: Vec<String>,
        school_bridge_subdomain: Option<String>,
    },
    DelegatedServiceAgentRunnerAccount {
        principal_natural_person_did: String,
        delegation_agreement_id: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MachineAccountSeatAssignment {
    pub seat_id: String,
    pub machine_hostname: String,
    pub os_account_username: String,
    pub webizen_profile_slug: String,
    pub principal_did: String,
    pub display_name: String,
    pub assignment_kind: SharedMachineAccountAssignmentKind,
    pub isolated_vault_rel_path: String,
    pub dedicated_loopback_port: u16,
    pub isolated_slg_arena_mib: u16,
    pub paired_mobile_pocket_cosigner_did: Option<String>,
    pub developed_identifiers: Vec<OnboardingIdentifierEvidence>,
    pub aggregate_confidence_permille: u16,
    pub confidence_tier: OnboardingConfidenceTier,
    pub receipt_quin: NQuin48,
}

pub fn evaluate_onboarding_identifiers_confidence(
    identifiers: &[OnboardingIdentifierEvidence],
) -> (u16, OnboardingConfidenceTier) {
    let mut attested_count = 0usize;
    let mut remainder_product_ppm: u128 = 1_000_000;

    for id in identifiers {
        if id.confidence_permille == 0 || id.confidence_permille >= 1000 {
            return (0, OnboardingConfidenceTier::RejectedDefinitiveCollapse);
        }
        if id.attested {
            attested_count += 1;
            let complement = 1000u128.saturating_sub(id.confidence_permille as u128);
            remainder_product_ppm = (remainder_product_ppm * complement) / 1000;
        }
    }

    if attested_count < 2 {
        return (350, OnboardingConfidenceTier::Tier0UnverifiedGuest);
    }

    let agg_permille = (1_000_000u128.saturating_sub(remainder_product_ppm) / 1000)
        .clamp(1, 999) as u16;

    let tier = if attested_count >= 4 && agg_permille >= 960 {
        OnboardingConfidenceTier::Tier3HighAssuranceMultiFactorPrincipal
    } else if attested_count >= 3 && agg_permille >= 880 {
        OnboardingConfidenceTier::Tier2DesktopAndMobilePaired
    } else if attested_count >= 2 && agg_permille >= 700 {
        OnboardingConfidenceTier::Tier1LocalApparatusBound
    } else {
        OnboardingConfidenceTier::Tier0UnverifiedGuest
    };

    (agg_permille, tier)
}

pub fn build_seeded_machine_onboarding_account_assignments() -> Vec<MachineAccountSeatAssignment> {
    let hostname = "mercer-homestead-workstation";
    let anvil_uri = "did:q42:anvil:10de-2684-99a1e4c2b7d01122";

    let make_seat = |seat_id: &str,
                     os_user: &str,
                     profile_slug: &str,
                     principal_did: &str,
                     display_name: &str,
                     assignment_kind: SharedMachineAccountAssignmentKind,
                     port: u16,
                     mobile_did: Option<&str>,
                     developed_identifiers: Vec<OnboardingIdentifierEvidence>|
     -> MachineAccountSeatAssignment {
        let (agg_permille, tier) =
            evaluate_onboarding_identifiers_confidence(&developed_identifiers);
        let receipt_quin = NQuin48::new(
            q_hash_u64(seat_id),
            q_hash_u64("onboarding:machineAccountSeatAssigned"),
            q_hash_u64(principal_did),
            q_hash_u64(profile_slug),
            agg_permille as u64,
        );
        MachineAccountSeatAssignment {
            seat_id: seat_id.to_string(),
            machine_hostname: hostname.to_string(),
            os_account_username: os_user.to_string(),
            webizen_profile_slug: profile_slug.to_string(),
            principal_did: principal_did.to_string(),
            display_name: display_name.to_string(),
            assignment_kind,
            isolated_vault_rel_path: format!(
                "/var/lib/webizen-host/sanctuary/seats/{profile_slug}/sanctuary_vault.cbor"
            ),
            dedicated_loopback_port: port,
            isolated_slg_arena_mib: 42,
            paired_mobile_pocket_cosigner_did: mobile_did.map(str::to_string),
            developed_identifiers,
            aggregate_confidence_permille: agg_permille,
            confidence_tier: tier,
            receipt_quin,
        }
    };

    vec![
        make_seat(
            "MACHINE-SEAT-01-ALEX-PERSONAL",
            "alex",
            "alex-personal-sanctuary",
            "did:webizen:person:alex-mercer",
            "Alex Mercer (Primary Personal Sanctuary & Homestead Steward)",
            SharedMachineAccountAssignmentKind::PrimaryPersonalSanctuaryAccount {
                household_role: "Father & Primary Workstation Steward".to_string(),
            },
            8080,
            Some("did:webizen:mobile-avf:alex-pixel9-pkvm"),
            vec![
                OnboardingIdentifierEvidence {
                    identifier_uri: anvil_uri.to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "desktop-anvil-np64-tpm-quote".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 620,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:q42:locus:alex-sanctuary-argon2id".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "argon2id-vault-lane-verifier".to_string(),
                    crypto_scheme: "BLAKE3-Commitment".to_string(),
                    attested: true,
                    confidence_permille: 720,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:webizen:mobile-avf:alex-pixel9-pkvm".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "mobile-avf-pkvm-el2-pocket-cosigner".to_string(),
                    crypto_scheme: "ML-DSA-65".to_string(),
                    attested: true,
                    confidence_permille: 780,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "qdp://alex.mercer-homestead.au#prior-history-corroborated".to_string(),
                    plane: "claim".to_string(),
                    modality_role: "qdp-domain-and-corroborated-prior-history".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 700,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "urn:webizen:shamir:alex-2of4-household-quorum".to_string(),
                    plane: "claim".to_string(),
                    modality_role: "shamir-guardian-social-co-attestation".to_string(),
                    crypto_scheme: "ML-DSA-65".to_string(),
                    attested: true,
                    confidence_permille: 650,
                },
            ],
        ),
        make_seat(
            "MACHINE-SEAT-02-ELENA-FIDUCIARY",
            "elena",
            "elena-clinical-fiduciary",
            "did:webizen:person:dr-elena-rostova",
            "Dr. Elena Rostova-Mercer (AHPRA Clinical Psychiatrist Fiduciary Account)",
            SharedMachineAccountAssignmentKind::ProfessionalFiduciaryPersonaAccount {
                sector: "HealthcareAndMedical".to_string(),
                qualification_credential_id: "AHPRA-MED0001849201".to_string(),
                jurisdiction_iso: "AU-VIC".to_string(),
            },
            8081,
            Some("did:webizen:mobile-avf:elena-pocket-cosigner"),
            vec![
                OnboardingIdentifierEvidence {
                    identifier_uri: anvil_uri.to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "desktop-anvil-np64-tpm-quote".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 620,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:q42:locus:elena-clinical-fiduciary-argon2id".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "argon2id-fiduciary-vault-lane".to_string(),
                    crypto_scheme: "BLAKE3-Commitment".to_string(),
                    attested: true,
                    confidence_permille: 740,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:webizen:mobile-avf:elena-pocket-cosigner".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "mobile-avf-pkvm-el2-pocket-cosigner".to_string(),
                    crypto_scheme: "ML-DSA-65".to_string(),
                    attested: true,
                    confidence_permille: 800,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "urn:ahpra:credential:MED0001849201".to_string(),
                    plane: "claim".to_string(),
                    modality_role: "fiduciary-qualification-ahpra-specialist".to_string(),
                    crypto_scheme: "ML-DSA-65".to_string(),
                    attested: true,
                    confidence_permille: 760,
                },
            ],
        ),
        make_seat(
            "MACHINE-SEAT-03-LEO-STUDENT",
            "leo",
            "leo-student-commons",
            "did:webizen:person:leo-mercer",
            "Leo Mercer (Child · Year 6 Student Seat with Guardian Co-Signers)",
            SharedMachineAccountAssignmentKind::ChildOrSupportedDependentAccount {
                agency_stage: "AgencyStage::Child (UN CRC Evolving Capacity)".to_string(),
                guardian_dids: vec![
                    "did:webizen:person:alex-mercer".to_string(),
                    "did:webizen:person:dr-elena-rostova".to_string(),
                ],
                school_bridge_subdomain: Some("school.leo.mercer-homestead.au".to_string()),
            },
            8082,
            Some("did:webizen:mobile-avf:alex-pixel9-pkvm"),
            vec![
                OnboardingIdentifierEvidence {
                    identifier_uri: anvil_uri.to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "desktop-anvil-np64-tpm-quote".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 600,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:q42:locus:leo-student-sanctuary-lane".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "argon2id-child-vault-lane".to_string(),
                    crypto_scheme: "BLAKE3-Commitment".to_string(),
                    attested: true,
                    confidence_permille: 680,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "urn:webizen:guardianship:leo-parental-co-attestation".to_string(),
                    plane: "claim".to_string(),
                    modality_role: "parental-guardian-cosigner-quorum".to_string(),
                    crypto_scheme: "ML-DSA-65".to_string(),
                    attested: true,
                    confidence_permille: 750,
                },
            ],
        ),
        make_seat(
            "MACHINE-SEAT-04-DELEGATED-AGENT",
            "alex",
            "alex-delegated-forge-agent",
            "did:qualia:subagent:alex-mercer:forge-assistant",
            "Alex's Delegated CAD & Ledger Sub-Agent (Non-Voting Instrument Seat)",
            SharedMachineAccountAssignmentKind::DelegatedServiceAgentRunnerAccount {
                principal_natural_person_did: "did:webizen:person:alex-mercer".to_string(),
                delegation_agreement_id: "AGR-AGENT-DELEGATION-ALEX".to_string(),
            },
            8083,
            None,
            vec![
                OnboardingIdentifierEvidence {
                    identifier_uri: anvil_uri.to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "desktop-anvil-np64-tpm-quote".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 550,
                },
                OnboardingIdentifierEvidence {
                    identifier_uri: "did:qualia:subagent:alex-mercer:forge-assistant".to_string(),
                    plane: "instrument".to_string(),
                    modality_role: "delegated-subagent-zcap-instrument".to_string(),
                    crypto_scheme: "Ed25519".to_string(),
                    attested: true,
                    confidence_permille: 650,
                },
            ],
        ),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn family_household_and_village_small_business_personal_vps_isolates_father_mother_works_and_child_school_bridges() {
        let vps = build_seeded_family_village_personal_vps();
        assert_eq!(
            vps.topology,
            PersonalVpsTopologyMode::HybridPairedLocalAndCloudVps
        );
        assert_eq!(vps.seats.len(), 4);
        assert_eq!(vps.family_works.len(), 3);
        assert_eq!(vps.school_bridges.len(), 2);

        assert!(matches!(
            vps.authorize_family_craft_work_operation(
                "WORK-FATHER-FORGE",
                "did:webizen:person:alex-mercer",
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::PermittedAdultCraftWork { .. }
        ));
        assert!(matches!(
            vps.authorize_family_craft_work_operation(
                "WORK-MOTHER-APOTHECARY",
                "did:webizen:person:alex-mercer",
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::BlockedFailClosed { .. }
        ));
        assert!(matches!(
            vps.authorize_family_craft_work_operation(
                "WORK-MOTHER-APOTHECARY",
                "did:webizen:person:dr-elena-rostova",
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::PermittedAdultCraftWork { .. }
        ));
        assert!(matches!(
            vps.authorize_family_craft_work_operation(
                "WORK-FAMILY-COMMONS",
                "did:webizen:person:dr-elena-rostova",
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::PermittedAdultCraftWork { .. }
        ));
        assert!(matches!(
            vps.authorize_family_craft_work_operation(
                "WORK-FATHER-FORGE",
                "did:webizen:person:leo-mercer",
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::BlockedFailClosed { .. }
        ));
        assert!(matches!(
            vps.evaluate_child_school_interaction(
                "did:webizen:person:leo-mercer",
                "melbourne-commons-school.edu.au",
                false,
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::PermittedGuardianApprovedSchoolExchange { .. }
        ));
        assert!(matches!(
            vps.evaluate_child_school_interaction(
                "did:webizen:person:leo-mercer",
                "melbourne-commons-school.edu.au",
                true,
                1_763_999_000
            ),
            FamilyVpsAccessOutcome::BlockedFailClosed { .. }
        ));

        // Verify Multi-Device Availability Mesh (Phone Elevator + Sleeping Laptop + Mac Mini Home Server / VPS Persistence)
        let mut mesh = build_seeded_multi_device_persistence_mesh();
        let env1 = mesh.dispatch_respecting_availability(
            "ENV-MAIL-01",
            "did:webizen:person:dr-elena-rostova",
            DispatchedPayloadKind::QdpRelationshipScopedMail,
            "Clinical Autonomic Follow-Up while laptop is offline",
            "sha256_mail_payload_01",
            false,
            1_763_999_000,
        );
        assert_eq!(
            env1.delivery_state,
            SpoolDeliveryState::SpooledAtRecipientPersistenceLayerAwaitingWorkstation
        );
        assert_eq!(
            env1.target_persistence_node_id.as_deref(),
            Some("DEV-MAC-MINI-HOME-SERVER")
        );

        let _env2 = mesh.dispatch_respecting_availability(
            "ENV-SETTLE-02",
            "did:webizen:person:marcus-vance",
            DispatchedPayloadKind::CooperativeProjectClaimOrSettlement,
            "Stage-8 Settlement Co-Sign Request (Requires Phone Elevation)",
            "sha256_settle_payload_02",
            true,
            1_763_999_000,
        );
        let st_elev = mesh
            .elevate_permission_on_phone("ENV-SETTLE-02", "ed25519_ml_dsa_87_phone_cosign_alex")
            .unwrap();
        assert_eq!(
            st_elev,
            SpoolDeliveryState::ElevatedByPhoneCosignerAwaitingWorkstationHydration
        );
        let drained = mesh.wake_workstation_and_drain_spool();
        assert_eq!(drained, 2);

        // Verify ATO Modulus-89 Australian ABN validator & Nominated VPS Installation
        assert_eq!(
            validate_australian_abn_mod89("51 824 753 556").unwrap(),
            "51 824 753 556"
        );
        assert!(validate_australian_abn_mod89("51 824 753 557").is_err());

        let nom = build_seeded_australian_abn_vps_nomination();
        let plan = instigate_nominated_vps_installation(&nom, 1_763_999_000).unwrap();
        assert!(plan.auto_gst_escrow_enabled);
        assert_eq!(plan.qcdn_cost_recovery_pool_target_cents, 54_000);
        assert!(plan.receipt_quin.verify_parity());

        let wsl_bridge = build_wsl2_linux_kernel_bridge_profile(true);
        assert!(wsl_bridge.ebpf_socket_quota_enforcement_active);
        assert!(wsl_bridge.nftables_deontic_split_horizon_active);
        let capsule = seal_windows_to_webizen_primary_os_migration_capsule(
            "did:webizen:person:alex-mercer",
            wsl_bridge.substrate_mode,
            4,
            3,
            2,
            "ed25519_ml_dsa_87_phone_cosign_primary_os_cutover_alex",
            1_763_999_000,
        )
        .unwrap();
        assert!(capsule.evidentiary_timestamps_preserved_across_os_wipe);
        assert!(capsule.receipt_quin.verify_parity());

        let seats = build_seeded_machine_onboarding_account_assignments();
        assert_eq!(seats.len(), 4);
        assert_eq!(
            seats[0].confidence_tier,
            OnboardingConfidenceTier::Tier3HighAssuranceMultiFactorPrincipal
        );
        assert_eq!(
            seats[1].confidence_tier,
            OnboardingConfidenceTier::Tier3HighAssuranceMultiFactorPrincipal
        );
        assert_eq!(
            seats[2].confidence_tier,
            OnboardingConfidenceTier::Tier2DesktopAndMobilePaired
        );
        assert_eq!(
            seats[3].confidence_tier,
            OnboardingConfidenceTier::Tier1LocalApparatusBound
        );
        assert!(seats.iter().all(|s| s.receipt_quin.verify_parity()));
    }
}
