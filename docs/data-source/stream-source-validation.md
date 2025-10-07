
## Selected Streaming Source: Faker-generated Hospital Transaction Data
- **Source:** Python scripts using the Faker library
- **Authentication:** Not required
- **Rate Limits:** Configurable (no external limits)
- **Data Format:** JSON (custom schema)
- **Rationale:** Enables development and testing of real-time pipeline features for healthcare transactions. Data can be generated on demand and customized for various hospital scenarios.

**Real-time Data Capability:**  
Faker scripts generate new, randomized hospital transaction records at configurable intervals, simulating real-time data ingestion for hospital billing and operations.

---

## Backup Options
*None required. The hospital transaction schema is stable and fully synthetic.*

---

## Testing Results
- [x] Faker data generation accessible
- [x] Data quality configurable
- [x] No rate limits
- [x] Documentation: [Faker library](https://faker.readthedocs.io/)

---

**Sample Output (Faker-generated hospital transaction):**
```json
{
  "transaction_id": "b1e2c3d4-5678-1234-9abc-1234567890ab",
  "patient_id": "a2b3c4d5-6789-2345-0bcd-2345678901bc",
  "admission_id": "c3d4e5f6-7890-3456-1cde-3456789012cd",
  "department": "Cardiology",
  "doctor": "Dr. Jane Smith",
  "service": "ECG",
  "cost": 350.75,
  "payment_method": "Insurance",
  "transaction_time": "2025-10-07T09:15:23.123456",
  "status": "Completed",
  "ingested_at": "2025-10-07T09:16:00.000000"
}
```

**Data Schema:**
- transaction_id (UUID)
- patient_id (UUID)
- admission_id (UUID)
- department (string)
- doctor (string)
- service (string)
- cost (float)
- payment_method (string)
- transaction_time (ISO timestamp string)
- status (string)
- ingested_at (ISO timestamp string)

---

**Summary:**
Faker-generated synthetic hospital transaction data is now used as the main streaming source for development and testing. It provides flexible, on-demand data generation for real-time pipeline validation in healthcare analytics. The schema is stable and tailored for hospital operations, with no external dependencies required.
