# Context Map

## Bounded Contexts

### 1. Anlagemanagement
> Responsible for the inventory management of Anlagen

### 2. Gebäudemanagement
> A Gebäude is a grouping of Wohneinheiten that belong to a specific part of the whole building.

### 3. Einheitmanagement
> Responsible for managing Wohneinheiten with their information. This is a typical inventory management.

### 4. Bauteilmanagement
> Responsible for grouping Wohneinheiten to Bauteile. This context is especially important for sales purposes. Projektinserate are crated based on the information of Bauteil.

### 5. Einheitinseratmanagement
> Responsible for managing all advertisements concerning one Wohneinheit.

### 6. Projektinseratmanagement
> Responsible for managing advertisements about projects. This kind of advertisements could contain multiple advertisements for Wohneinheiten. For potential tenants it is possible to place a Vormerkung for a Projektinserat.

### 7. Inseratsuche
> Responsible for searching advertisements. Users that use the search can search by Address, postcode, contract type, area and more. Searches can be saved as Suchagent. Suchagenten will notify its creator about new advertisements that match the search parameters.

### 8. Bewerbungen
> Responsible for handling applications to Einheitinserate. People from the real estate backoffice are able to check and approve incoming Bewerbungen. Potential tenants are abel to apply for an Inserat as soon as a dedicated salesperson opens up the application phase for that person.

### 9. Vertragsverwaltung
> Responsible for all types of contract management. Wether it is adding contracts to a Wohneinheit, cancel contracts or other businesses concerning contracts

### 10. Schadensmeldungen
> Responsible for recording Schadensmeldungen. Schadensmeldungen record issues on different levels of a building.

### 11. Begehungen
> Responsible for managing inspections of Anlagen. It records which Anlagen need inspections and their resulting reports.

### 12. Aufträge
> Responsible for creating Workorders (= Aufträge). All Aufträge originate from a dedicated source like Schadensmeldung, Begehungen or others

### 13. Ausstattungen
> Responsible for managing the inventory of Ausstattungen on all levels of a building.

### 14. Lieferanten
> Responsbile for managing the inventory of available Lieferanten.

### 15. Zuständigkeiten
> Responsible for managing the responsible persons for a dedicated Anlage. Employees can have different types of responsibilities like property management, technical responsibility etc.

### 16. Messaging
> Responsible for sending given content over selected communication channels

### 17. Customerrelation
> Responsible for creating communication items that are then distributed to a set of customers

---

## Relationships

| # | Upstream | Downstream | Type | Clarity | Notes |
|---|----------|------------|------|---------|-------|
| 1 | Einheitmanagement | Ausstattungen | Open Host Service (OHS) | - | Ausstattungen references Einheit context |
| 2 | Gebäudemanagement | Ausstattungen | Open Host Service (OHS) | - | Ausstattungen references Gebäude context |
| 3 | Anlagemanagement | Ausstattungen | Open Host Service (OHS) | - | Ausstattungen references Anlage context |
| 4 | Anlagemanagement | Gebäudemanagement | Open Host Service (OHS) | - | Gebäude references stable AnlageId |
| 5 | Zuständigkeiten | Anlagemanagement | Open Host Service (OHS) | - | Responsibility data enriches Anlage |
| 6 | Einheitmanagement | Gebäudemanagement | Open Host Service (OHS) | - | Einheiten grouped into Gebäude |
| 7 | Anlagemanagement | Bauteilmanagement | Open Host Service (OHS) | - | Bauteil consumes Anlage identity |
| 8 | Bauteilmanagement | Projektinseratmanagement | Open Host Service (OHS) | - | Projektinserat composes Wohneinheiten grouped via Bauteil |
| 9 | Einheitmanagement | Einheitinseratmanagement | Customer-Supplier (CS) U:OHS D:ACL | - | New — Inserat needs Einheit details and reacts to availability changes |
| 10 | Einheitmanagement | Bauteilmanagement | Open Host Service (OHS) | - | Bauteil composes Einheiten across Gebäude |
| 11 | Einheitmanagement | Projektinseratmanagement | Open Host Service (OHS) | - | New — Projektinserat displays per-Einheit details |
| 12 | Einheitinseratmanagement | Bewerbungen | Open Host Service (OHS) | - | Applications reference which Inserat |
| 13 | Einheitinseratmanagement | Inseratsuche | Open Host Service (OHS) | - | Search consumes published advertisements |
| 14 | Projektinseratmanagement | Inseratsuche | Open Host Service (OHS) | - | Search consumes published advertisements |
| 15 | Begehungen | Aufträge | Open Host Service (OHS) | - | Critical inspection results trigger workorder creation |
| 16 | Zuständigkeiten | Aufträge | Open Host Service (OHS) | - | Future — for notification routing on workorder events |
| 17 | Schadensmeldungen | Aufträge | Open Host Service (OHS) | - | Damage reports trigger workorder creation |
| 18 | Einheitmanagement | Schadensmeldungen | Open Host Service (OHS) | - | Damage reports at Einheit level |
| 19 | Gebäudemanagement | Schadensmeldungen | Open Host Service (OHS) | - | Damage reports at Gebäude level |
| 20 | Anlagemanagement | Schadensmeldungen | Open Host Service (OHS) | - | Damage reports at Anlage level |
| 21 | Zuständigkeiten | Begehungen | Conformist (CF) | - | Used to assign Begehungsbeauftragungen to responsible persons |
| 22 | Lieferanten | Aufträge | Open Host Service (OHS) | - | Aufträge consume Kreditor catalog |
| 23 | Vertragsverwaltung | Einheitmanagement | Open Host Service (OHS) | - | Signed contracts update Einheit occupancy; Einheitmanagement is single source of truth for availability |
| 24 | Zuständigkeiten | Schadensmeldungen | Open Host Service (OHS) | - | Future — for notification routing on damage report events |
| 25 | Anlagemanagement | Customerrelation | Customer-Supplier (CS) U:OHS D:CF | - | - |
| 26 | Anlagemanagement | Begehungen | Open Host Service (OHS) | - | Begehungen projects only required Anlage attributes into its own Begehungsbeauftragung aggregate |
| 27 | Messaging | Aufträge | Customer-Supplier (CS) U:OHS D:CF | - | - |
| 28 | Messaging | Customerrelation | Customer-Supplier (CS) U:OHS D:CF | - | - |

---

## Summary

- **Total Bounded Contexts:** 17
- **Total Relationships:** 28
- **Relationship Breakdown:** Open Host Service: 23, Customer-Supplier: 4, Conformist: 1
