# Draft Definition File: Semantic Timeline & Artifact Matrix
**Application:** wellfare
**Module:** Semantic Timeline (Calendar & Event Management)
**Purpose:** To define a computationally active temporal system that manages appointments, logs event data, and dynamically links physical/digital artifacts (e.g., pathology samples) to downstream medical capabilities.

---

## 1. Core Structural Paradigm: The Temporal Graph

The calendar does not exist as a separate database. It functions as a temporal UI view of the core **RDF-Star graph**. 

*   **Temporal Nodes:** Every appointment, event, or medical procedure is instantiated as a temporal node with definitive start/end timestamps.
*   **Contextual Binding:** These nodes are cryptographically linked to specific agents within the **Social Book** (e.g., the specific phlebotomist or clinic) and to relevant conversations in the **Secure Communications Matrix**.
*   **Sanctuary Integration:** Events can be logged as public (Standard Graph) or hidden (**Veiled Assertions** in Sanctuary Mode). For example, an appointment at a rehab clinic can be temporally blocked out in the standard UI as "Busy," while the true nature of the appointment is only resolvable in Sanctuary Mode.

---

## 2. Artifact Generation & Linkage (The Pathology Use-Case)

The defining feature of this system is its ability to track the material consequences of an event. When an appointment occurs, it can generate "Artifacts."

*   **Event Instantiation:** The user attends a blood draw. The event node is marked as `Completed`.
*   **Artifact Creation:** The event generates a linked Semantic Artifact (e.g., `Specimen_Blood_01`). 
*   **Metadata Tagging:** This artifact is tagged with highly specific RDF properties:
    *   `labReferenceNumber`: [Alpha-Numeric ID provided by the lab]
    *   `collectionDate`: [Timestamp]
    *   `availableVolume`: [e.g., 15ml]
    *   `degradationTimeline`: [e.g., Expires in 7 days]
*   **Downstream Utility:** If a doctor subsequently realizes they forgot to order a specific test (e.g., a Thyroid Panel), their diagnostic agent can query the user's vault. The Prolog engine evaluates the `Specimen_Blood_01` artifact, confirms the `availableVolume` is sufficient and the `degradationTimeline` has not passed, and outputs the `labReferenceNumber` so the doctor can append the test without requiring the user to undergo another physical blood draw.

---

## 3. Prolog-Driven Scheduling & Logistics

The local logic engine continuously monitors the Semantic Timeline to assist the user proactively.

*   **Prerequisite Auditing:** If an upcoming appointment requires prerequisites (e.g., "Fasting for 12 hours" or "Must complete MRI prior to surgical consult"), the Prolog engine maps the timeline to ensure these conditions are met. If the MRI node is missing or scheduled *after* the consult, it throws an internal alert.
*   **Travel & Geofencing Coordination:** By cross-referencing the appointment's physical location with the user's encrypted GPS timeline, the engine can estimate necessary travel times or block out transit windows.
*   **Resource Collision Avoidance:** The engine prevents logical impossibilities, such as scheduling a physically demanding task immediately following an event tagged as a "sedated procedure."

---

## 4. Shared Events & Granular Visibility

Because events involve external agents, the calendar must support the same granulated permissions as the communications module.

*   **Permissioned Invites:** When an appointment is scheduled with a verified agent from the Social Book, a cryptographic handshake occurs. The event is synced to their system utilizing the Nymtech mixnet.
*   **Contextual Cloaking:** A user can grant an advocate (e.g., a social worker) partial visibility. The advocate's calendar view might show the user is at a "Medical Appointment" at 2:00 PM, but the specific details (the doctor's identity, the clinic, and the pathology data) remain entirely masked by the vault's access controls.

---

## 5. Dependent Activity Chaining & Expected Results Timelines

To support complex healthcare journeys, the calendar and event logs must model time-linked dependencies and expected delays between events, activities, and data releases.

### 5.1 Chained Medical Workflows (Directed Acyclic Graphs of Events)
Events are modeled not just as isolated timeline entries, but as nodes in a sequential dependency chain (DAG).
*   **Prerequisites & Dependents:** An event (e.g., "Follow-up GP Consult") is marked as dependent on a prior event ("Diagnostic Test Results Delivered"), which itself depends on another event ("Blood Sample Collection").
*   **Logical Audits:** The local Prolog engine checks the graph and flags logical order violations (e.g. scheduling the follow-up consult *before* the scheduled lab results delivery date).

### 5.2 Expected Result Delays & SLA Tracking
When an event (like a pathology collection) occurs, the system records the expected duration (SLA) before the results are delivered:
*   **Expected Results Timeline:** The event is tagged with an expected delay property, e.g. `expectedResultLag: "2 days"`.
*   **SLA Warning Switch:** The system generates an expected results delivery node in the calendar: `Expected Results: Laverty Lipid Panel` on ` collectionDate + expectedResultLag `.
*   **Escalation Alerts:** If the results are not delivered by the expected delivery date, the Prolog engine flags a delivery delay, notifying the user to contact the lab or clinic.

### 5.3 Concrete Workflow Scenario: GP-Lab-GP Consultation Loop
To illustrate the dependency system, consider the common diagnostic cycle:
1.  **Step 1: Initial GP Consult (`ev-1`)**: The user visits their GP (e.g., Dr. Sarah Jenkins), who orders pathology tests.
2.  **Step 2: Pathology Collection (`ev-2`)**: The user goes to a pathology lab (e.g., Laverty Pathology) to have blood drawn.
    *   *Metadata*: This event specifies `producesArtifact: true` and defines `expectedResultLag: "48 hours"`.
3.  **Step 3: Pathology Results Ingestion (`ev-3`)**: The expected ingestion event is automatically generated on the calendar for `Collection Date + 48 hours`.
    *   *Dependency*: `ev-3` depends on `ev-2`.
4.  **Step 4: Follow-up GP Consult (`ev-4`)**: The user schedules a consultation to review the results with the doctor.
    *   *Dependency*: `ev-4` has a prerequisite rule requiring `ev-3` to be completed.
5.  **Prolog Auditor Rule Validation**:
    *   If the user schedules `ev-4` at `Collection Date + 24 hours` (before the 48-hour results ingestion SLA has elapsed), the auditor evaluates the rules:
        `prereq_not_met(ev-4, ev-3) :- date_of(ev-4, D4), expected_delivery(ev-3, D3), D4 < D3.`
    *   The system flags a calendar conflict, notifying the user to push back the follow-up consult.

---

## 6. Semantic Tasks & Action Items (To-Do Integration)

To support active self-management of health journeys, the temporal graph integrates Tasks alongside Events. While Events represent point-in-time appointments or clinical processes, Tasks represent actions the user must take.

### 6.1 Task Ontology & Graph Representation
Tasks are modeled as a subclass of `Activity` in the RDF-star graph:
*   **Properties**:
    *   `associatedEvent`: Links a task to a parent event (e.g., fasting is associated with a blood draw).
    *   `dependsOnTask`: Creates task-to-task dependency chains (e.g., "pick up referral paper" must precede "attend lab").
    *   `dueDate` / `dueTime`: The target timestamp for completion.
    *   `taskStatus`: String enum (`Pending`, `InProgress`, `Completed`, `Overdue`).
*   **RDF-Star Assertion Example**:
    ```turtle
    << :Task_Fasting_01 :associatedEvent :SpecimenCollection_01 >>
        :taskStatus "Pending" ;
        :dueDate "2026-05-30T08:00:00Z"^^xsd:dateTime .
    ```

### 6.2 Automatic Constraint & Preparation Generator
The Prolog logic engine automatically synthesizes preparation tasks when specific events are scheduled:
*   **Fasting Rule**:
    `create_preparation_task(EvId, "12-Hour Fasting", DueTime) :- is_pathology_collection(EvId), test_requires_fasting(EvId), date_of(EvId, CollTime), subtract_hours(CollTime, 12, DueTime).`
*   **Referral Collection Rule**:
    `create_preparation_task(EvId, "Bring GP Referral Paperwork", CollTime) :- is_pathology_collection(EvId), date_of(EvId, CollTime).`
*   **Prerequisite Warning**: If a task remains `Pending` past its due date, the system flags the parent event as "At Risk" (e.g., going for a test without fasting will lead to invalid results).

