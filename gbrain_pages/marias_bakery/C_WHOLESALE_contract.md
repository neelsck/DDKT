---
type: contract-fsm
title: "Maria's Bakery - C WHOLESALE contract"
tags: [marias-bakery, contract-fsm, executable-contract, fsm]
contract_id: C_WHOLESALE_contract
source_file: output/C_WHOLESALE_contract/fsm.json
---

# Maria's Bakery - C WHOLESALE contract

This page ingests the finite state machine JSON for `C_WHOLESALE_contract`. The app uses this as contract-grounded retrieval context, then verifies proposed scenarios by replaying events through the FSM.

## Contract Facts

- Parties: Bakery, Customer, Maria's Bakery LLC, Three Oaks Cafe Group LLC
- Initial state: `ACTIVE`
- State count: 8
- Transition count: 13
- Amounts: {"late_delivery_credit": "250", "monthly_route_price": "18000"}
- Thresholds: {"at_risk_threshold_late_or_missed": 3, "immediate_termination_threshold_missed": 3}

## States

| State | Terminal | Description |
|---|---:|---|
| `ACTIVE` | False | Bakery performing daily deliveries, all obligations current |
| `LATE_DELIVERY_RECORDED` | False | One or more late deliveries recorded, credit applied but contract continues |
| `AT_RISK` | False | Three or more late/missed deliveries in rolling month, at-risk notice issued |
| `IN_CURE` | False | Bakery has 10 days to present and begin executing cure plan |
| `INVOICE_PENDING` | False | Invoice issued, awaiting payment within 15-day term |
| `PAYMENT_OVERDUE` | False | Customer has not paid within 15 days of invoice |
| `TERMINATION_NOTICE_GIVEN` | False | Either party has given 30-day termination notice |
| `TERMINATED` | True | Agreement terminated, final settlement complete |

## Transitions

| Transition | Event | From | To | Guard | Effects |
|---|---|---|---|---|---|
| TR1 | `delivery_late` | `ACTIVE`, `LATE_DELIVERY_RECORDED`, `AT_RISK`, `IN_CURE` | `LATE_DELIVERY_RECORDED` | `late_count < 3` | PAYMENT: Credit Customer $250 for late delivery |
| TR2 | `at_risk_threshold_reached` | `ACTIVE`, `LATE_DELIVERY_RECORDED` | `AT_RISK` | `late_or_missed_count >= 3` |  |
| TR3 | `at_risk_notice_issued` | `AT_RISK` | `IN_CURE` |  | CURE_WINDOW: Bakery has 10 days to present and begin cure plan |
| TR4 | `cure_completed` | `IN_CURE` | `ACTIVE` |  |  |
| TR5 | `cure_failed` | `IN_CURE` | `TERMINATION_NOTICE_GIVEN` |  |  |
| TR6 | `invoice_issued` | `ACTIVE`, `LATE_DELIVERY_RECORDED`, `AT_RISK`, `IN_CURE` | `INVOICE_PENDING` |  |  |
| TR7 | `payment_received` | `INVOICE_PENDING` | `ACTIVE` | `days_since_invoice <= 15` | PAYMENT: Customer pays undisputed invoice amount within 15 days |
| TR8 | `payment_deadline_exceeded` | `INVOICE_PENDING` | `PAYMENT_OVERDUE` | `days_since_invoice > 15` |  |
| TR9 | `late_payment_received` | `PAYMENT_OVERDUE` | `ACTIVE` |  | PAYMENT: Customer pays overdue invoice amount |
| TR10 | `termination_notice_issued` | `ACTIVE`, `LATE_DELIVERY_RECORDED`, `AT_RISK`, `IN_CURE`, `INVOICE_PENDING`, `PAYMENT_OVERDUE` | `TERMINATION_NOTICE_GIVEN` |  |  |
| TR11 | `immediate_termination` | `ACTIVE`, `LATE_DELIVERY_RECORDED`, `AT_RISK` | `TERMINATED` | `consecutive_missed_deliveries >= 3` | PAYMENT: Customer pays earned amounts minus credits and offsets upon termination |
| TR12 | `termination_effective` | `TERMINATION_NOTICE_GIVEN` | `TERMINATED` | `days_since_notice >= 30` | PAYMENT: Customer pays earned amounts minus credits and offsets upon termination |
| TR13 | `performance_restored` | `LATE_DELIVERY_RECORDED` | `ACTIVE` | `late_count < 3` |  |

## Original Contract Text

```text
WHOLESALE BREAKFAST DELIVERY AGREEMENT

This Wholesale Breakfast Delivery Agreement (this "Agreement") is entered
into as of December 31, 2026, by and between Maria's Bakery LLC, a California
limited liability company ("Bakery"), and Three Oaks Cafe Group LLC, a
California limited liability company ("Customer").

1. APPOINTMENT AND ROUTE

1.1 Appointment. Customer appoints Bakery as a non-exclusive supplier of
breakfast pastries, bread, and related bakery products for the Customer
locations listed on Exhibit A.

1.2 Route Launch. The initial route start date is January 1, 2027. The
parties may adjust the start date only by written agreement.

1.3 No Franchise or Agency. Bakery is an independent contractor and is not a
franchisee, partner, employee, or agent of Customer.

2. PRODUCTS

2.1 Products. Bakery shall supply the products, pack sizes, and daily order
quantities agreed by the parties in writing.

2.2 Quality. Products shall be fresh, merchantable, properly packaged, and
prepared in compliance with applicable food-safety requirements.

2.3 Substitutions. Bakery shall not make material substitutions without
Customer's consent, except for emergency substitutions that are commercially
reasonable and comparable in quality.

3. DELIVERY OBLIGATION

3.1 Delivery Deadline. Bakery shall deliver conforming breakfast orders to
the applicable Customer location by 7:00 a.m. each weekday.

3.2 Late Delivery. A delivery after 7:00 a.m. is late unless Customer waives
the delay in writing.

3.3 Delivery Records. Bakery shall maintain delivery logs showing departure
time, arrival time, receiving location, and any shortage or rejection.

3.4 No Automatic Excuse. Vehicle unavailability, supplier issues, staffing
shortfalls, traffic, or insurance delays do not excuse late delivery unless
Customer gives a written waiver.

4. PRICE AND PAYMENT

4.1 Monthly Route Price. Customer shall pay Bakery $18,000.00 per calendar
month for the route if Bakery performs the month without termination.

4.2 Invoice. Bakery shall invoice monthly. Customer shall pay undisputed
amounts within fifteen days after receipt of invoice.

4.3 Disputes. Customer may dispute an invoice item in good faith by written
notice. Undisputed amounts remain payable.

5. LATE DELIVERY CREDIT

5.1 Credit Amount. Bakery shall credit Customer $250.00 for each late
delivery.

5.2 Application. Credits may be applied against the next invoice or paid by
Bakery if no further invoice will be issued.

5.3 No Waiver. A late-delivery credit is a price adjustment and does not
waive Customer's termination rights or other remedies.

6. AT-RISK STATUS; CURE; TERMINATION

6.1 At-Risk Status. If Bakery has three late or missed deliveries in a
rolling calendar month, Customer may place the account at-risk by written
notice.

6.2 Cure. Bakery shall have ten days after at-risk notice to present and
begin a commercially reasonable cure plan, including vehicle, driver,
ingredient, or loading corrections as applicable.

6.3 Termination. Customer may terminate this Agreement if Bakery fails to
cure within the cure period or if Customer elects immediate termination after
the third miss in a rolling calendar month.

6.4 Effect of Termination. Upon termination, Customer shall pay undisputed
amounts earned before termination, less credits and offsets permitted by this
Agreement.

7. FOOD SAFETY; REJECTION

Customer may reject products that are materially nonconforming, unsafe,
damaged, late, improperly packaged, or delivered outside agreed temperature or
freshness requirements. Rejection of nonconforming products does not limit the
late-delivery credit if the delivery was late.

8. INSURANCE

Bakery shall maintain commercial general liability, commercial auto liability,
and any cargo or spoilage coverage reasonably appropriate for refrigerated
food delivery. Customer may request certificates of insurance.

9. CONFIDENTIALITY

Customer pricing, location volume, route information, and promotional plans
are confidential. Bakery shall use such information only to perform this
Agreement.

10. RELATIONSHIP DISCRETION

Customer may waive isolated misses, late deliveries, or shortages in writing.
A waiver for one event does not waive future events or modify the Agreement.

11. TERM

This Agreement begins on the effective date and continues month to month
unless terminated under Section 6 or by either party on thirty days' written
notice after the first three months.

12. MISCELLANEOUS

This Agreement may be amended only in writing. Neither party may assign this
Agreement without the other party's consent except in connection with a sale
of substantially all assets or a merger. California law governs.

BAKERY:
Maria's Bakery LLC

CUSTOMER:
Three Oaks Cafe Group LLC
```

## Raw FSM JSON

```json
{
  "contract_id": "C_WHOLESALE_contract",
  "parties": [
    "Bakery",
    "Customer",
    "Maria's Bakery LLC",
    "Three Oaks Cafe Group LLC"
  ],
  "initial_state": "ACTIVE",
  "params": {
    "parties": [
      "Bakery",
      "Customer",
      "Maria's Bakery LLC",
      "Three Oaks Cafe Group LLC"
    ],
    "base_dates": {
      "effective_date": "2026-12-31",
      "route_start_date": "2027-01-01",
      "invoice_receipt_date": null,
      "at_risk_notice_date": null,
      "termination_date": null
    },
    "amounts": {
      "monthly_route_price": "18000",
      "late_delivery_credit": "250"
    },
    "rates": {},
    "durations": {
      "delivery_deadline_time": "07:00",
      "payment_term_days": 15,
      "cure_period_days": 10,
      "termination_notice_days": 30,
      "first_three_months_days": 90,
      "rolling_calendar_month_days": 30
    },
    "thresholds": {
      "at_risk_threshold_late_or_missed": 3,
      "immediate_termination_threshold_missed": 3
    }
  },
  "states": [
    {
      "id": "ACTIVE",
      "description": "Bakery performing daily deliveries, all obligations current",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "LATE_DELIVERY_RECORDED",
      "description": "One or more late deliveries recorded, credit applied but contract continues",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R13",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "AT_RISK",
      "description": "Three or more late/missed deliveries in rolling month, at-risk notice issued",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R13",
        "R17",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "IN_CURE",
      "description": "Bakery has 10 days to present and begin executing cure plan",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R13",
        "R17",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "INVOICE_PENDING",
      "description": "Invoice issued, awaiting payment within 15-day term",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R11",
        "R13",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "PAYMENT_OVERDUE",
      "description": "Customer has not paid within 15 days of invoice",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R11",
        "R13",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28",
        "R33"
      ]
    },
    {
      "id": "TERMINATION_NOTICE_GIVEN",
      "description": "Either party has given 30-day termination notice",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R3",
        "R5",
        "R7",
        "R9",
        "R10",
        "R11",
        "R13",
        "R20",
        "R23",
        "R24",
        "R25",
        "R27",
        "R28"
      ]
    },
    {
      "id": "TERMINATED",
      "description": "Agreement terminated, final settlement complete",
      "terminal": true,
      "active_rule_ids": [
        "R27",
        "R28"
      ]
    }
  ],
  "transitions": [
    {
      "id": "TR1",
      "from_states": [
        "ACTIVE",
        "LATE_DELIVERY_RECORDED",
        "AT_RISK",
        "IN_CURE"
      ],
      "to_state": "LATE_DELIVERY_RECORDED",
      "event_type": "delivery_late",
      "guard": "late_count < 3",
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "late_delivery_credit",
          "payment_from": "Bakery",
          "payment_to": "Customer",
          "cap": null,
          "description": "Credit Customer $250 for late delivery"
        }
      ],
      "description": "Delivery after 7:00 a.m. without waiver triggers late delivery credit"
    },
    {
      "id": "TR2",
      "from_states": [
        "ACTIVE",
        "LATE_DELIVERY_RECORDED"
      ],
      "to_state": "AT_RISK",
      "event_type": "at_risk_threshold_reached",
      "guard": "late_or_missed_count >= 3",
      "effects": [],
      "description": "Three or more late/missed deliveries in rolling calendar month triggers at-risk status"
    },
    {
      "id": "TR3",
      "from_states": [
        "AT_RISK"
      ],
      "to_state": "IN_CURE",
      "event_type": "at_risk_notice_issued",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "CURE_WINDOW",
          "duration_days": 10,
          "description": "Bakery has 10 days to present and begin cure plan"
        }
      ],
      "description": "Customer issues at-risk notice, opening 10-day cure window"
    },
    {
      "id": "TR4",
      "from_states": [
        "IN_CURE"
      ],
      "to_state": "ACTIVE",
      "event_type": "cure_completed",
      "guard": null,
      "effects": [],
      "description": "Bakery successfully presents and begins cure plan, returns to active status"
    },
    {
      "id": "TR5",
      "from_states": [
        "IN_CURE"
      ],
      "to_state": "TERMINATION_NOTICE_GIVEN",
      "event_type": "cure_failed",
      "guard": null,
      "effects": [],
      "description": "Bakery fails to cure within 10 days, Customer may terminate"
    },
    {
      "id": "TR6",
      "from_states": [
        "ACTIVE",
        "LATE_DELIVERY_RECORDED",
        "AT_RISK",
        "IN_CURE"
      ],
      "to_state": "INVOICE_PENDING",
      "event_type": "invoice_issued",
      "guard": null,
      "effects": [],
      "description": "Bakery issues monthly invoice at end of calendar month"
    },
    {
      "id": "TR7",
      "from_states": [
        "INVOICE_PENDING"
      ],
      "to_state": "ACTIVE",
      "event_type": "payment_received",
      "guard": "days_since_invoice <= 15",
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "undisputed_amount",
          "payment_from": "Customer",
          "payment_to": "Bakery",
          "cap": null,
          "description": "Customer pays undisputed invoice amount within 15 days"
        }
      ],
      "description": "Customer pays invoice within 15-day term"
    },
    {
      "id": "TR8",
      "from_states": [
        "INVOICE_PENDING"
      ],
      "to_state": "PAYMENT_OVERDUE",
      "event_type": "payment_deadline_exceeded",
      "guard": "days_since_invoice > 15",
      "effects": [],
      "description": "Customer fails to pay within 15 days of invoice receipt"
    },
    {
      "id": "TR9",
      "from_states": [
        "PAYMENT_OVERDUE"
      ],
      "to_state": "ACTIVE",
      "event_type": "late_payment_received",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "undisputed_amount",
          "payment_from": "Customer",
          "payment_to": "Bakery",
          "cap": null,
          "description": "Customer pays overdue invoice amount"
        }
      ],
      "description": "Customer makes overdue payment"
    },
    {
      "id": "TR10",
      "from_states": [
        "ACTIVE",
        "LATE_DELIVERY_RECORDED",
        "AT_RISK",
        "IN_CURE",
        "INVOICE_PENDING",
        "PAYMENT_OVERDUE"
      ],
      "to_state": "TERMINATION_NOTICE_GIVEN",
      "event_type": "termination_notice_issued",
      "guard": null,
      "effects": [],
      "description": "Either party issues 30-day termination notice"
    },
    {
      "id": "TR11",
      "from_states": [
        "ACTIVE",
        "LATE_DELIVERY_RECORDED",
        "AT_RISK"
      ],
      "to_state": "TERMINATED",
      "event_type": "immediate_termination",
      "guard": "consecutive_missed_deliveries >= 3",
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "earned_amount - credits - offsets",
          "payment_from": "Customer",
          "payment_to": "Bakery",
          "cap": null,
          "description": "Customer pays earned amounts minus credits and offsets upon termination"
        }
      ],
      "description": "Three consecutive missed deliveries triggers immediate termination"
    },
    {
      "id": "TR12",
      "from_states": [
        "TERMINATION_NOTICE_GIVEN"
      ],
      "to_state": "TERMINATED",
      "event_type": "termination_effective",
      "guard": "days_since_notice >= 30",
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "earned_amount - credits - offsets",
          "payment_from": "Customer",
          "payment_to": "Bakery",
          "cap": null,
          "description": "Customer pays earned amounts minus credits and offsets upon termination"
        }
      ],
      "description": "30-day notice period expires, final settlement executed"
    },
    {
      "id": "TR13",
      "from_states": [
        "LATE_DELIVERY_RECORDED"
      ],
      "to_state": "ACTIVE",
      "event_type": "performance_restored",
      "guard": "late_count < 3",
      "effects": [],
      "description": "Performance improves below at-risk threshold, returns to normal active state"
    }
  ],
  "rules": [
    {
      "id": "R1",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Supply agreed products",
      "activation": "INACTIVE",
      "description": "Bakery shall supply the products, pack sizes, and daily order quantities agreed by the parties in writing.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T1",
          "type": "EVENT_TRIGGER",
          "condition": "Products, pack sizes, and daily order quantities agreed by parties in writing"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R3",
      "type": "PROHIBITION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Make material substitutions without consent",
      "activation": "INACTIVE",
      "description": "Bakery shall not make material substitutions without Customer's consent, except for emergency substitutions that are commercially reasonable and comparable in quality.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T3",
          "type": "EVENT_TRIGGER",
          "condition": "Need for material substitution arises"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": [
        "R4"
      ]
    },
    {
      "id": "R5",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Deliver breakfast orders by deadline",
      "activation": "INACTIVE",
      "description": "Bakery shall deliver conforming breakfast orders to the applicable Customer location by 7:00 a.m. each weekday.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T5",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Each weekday during contract term",
          "reference_date": "route_start_date"
        }
      ],
      "effects": [
        {
          "id": "E1",
          "type": "RULE_ACTIVATION",
          "description": "If delivery is after 7:00 a.m. without waiver, delivery is late and triggers late delivery credit",
          "target_rule_id": "R9",
          "new_state": "LATE_DELIVERY"
        }
      ],
      "constraints": [
        {
          "id": "C1",
          "type": "GRACE_PERIOD",
          "duration": "until 7:00 a.m.",
          "scope": [
            "R5"
          ],
          "description": "Delivery must occur by 7:00 a.m. each weekday"
        }
      ],
      "exceptions": [
        "R6"
      ]
    },
    {
      "id": "R7",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Maintain delivery logs",
      "activation": "INACTIVE",
      "description": "Bakery shall maintain delivery logs showing departure time, arrival time, receiving location, and any shortage or rejection.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T7",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation for all deliveries",
          "reference_date": "route_start_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R9",
      "type": "OBLIGATION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Pay monthly route price",
      "activation": "INACTIVE",
      "description": "Customer shall pay Bakery $18,000.00 per calendar month for the route if Bakery performs the month without termination.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T9",
          "type": "CONDITION_PRECEDENT",
          "condition": "Bakery performs the month without termination"
        }
      ],
      "effects": [
        {
          "id": "E3",
          "type": "PAYMENT",
          "description": "Customer pays Bakery $18,000.00 per calendar month",
          "payment_formula": "18000",
          "payment_from": "Customer",
          "payment_to": "Bakery"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R10",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Invoice monthly",
      "activation": "INACTIVE",
      "description": "Bakery shall invoice monthly.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T10",
          "type": "TEMPORAL_TRIGGER",
          "condition": "End of each calendar month",
          "reference_date": "route_start_date"
        }
      ],
      "effects": [
        {
          "id": "E4",
          "type": "RULE_ACTIVATION",
          "description": "Invoice triggers payment obligation",
          "target_rule_id": "R11"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R11",
      "type": "OBLIGATION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Pay undisputed invoice amounts",
      "activation": "INACTIVE",
      "description": "Customer shall pay undisputed amounts within fifteen days after receipt of invoice.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T11",
          "type": "EVENT_TRIGGER",
          "condition": "Receipt of invoice from Bakery",
          "reference_date": "invoice_receipt_date",
          "duration": "15 days",
          "duration_days": 15
        }
      ],
      "effects": [
        {
          "id": "E5",
          "type": "PAYMENT",
          "description": "Customer pays undisputed invoice amounts",
          "payment_formula": "undisputed_amount",
          "payment_from": "Customer",
          "payment_to": "Bakery"
        }
      ],
      "constraints": [
        {
          "id": "C2",
          "type": "GRACE_PERIOD",
          "duration": "15 days",
          "duration_days": 15,
          "scope": [
            "R11"
          ],
          "description": "Payment due within 15 days after receipt of invoice"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R13",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Credit for each late delivery",
      "activation": "INACTIVE",
      "description": "Bakery shall credit Customer $250.00 for each late delivery.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T13",
          "type": "EVENT_TRIGGER",
          "condition": "Delivery occurs after 7:00 a.m. without written waiver"
        }
      ],
      "effects": [
        {
          "id": "E6",
          "type": "PAYMENT",
          "description": "Bakery credits Customer $250.00 per late delivery",
          "payment_formula": "250",
          "payment_from": "Bakery",
          "payment_to": "Customer"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R17",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Present and begin cure plan",
      "activation": "INACTIVE",
      "description": "Bakery shall have ten days after at-risk notice to present and begin a commercially reasonable cure plan, including vehicle, driver, ingredient, or loading corrections as applicable.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T17",
          "type": "EVENT_TRIGGER",
          "condition": "Receipt of at-risk notice from Customer",
          "reference_date": "at_risk_notice_date",
          "duration": "10 days",
          "duration_days": 10
        }
      ],
      "effects": [
        {
          "id": "E9",
          "type": "CURE_WINDOW",
          "description": "Bakery has 10-day window to present and begin cure plan",
          "new_state": "CURING"
        }
      ],
      "constraints": [
        {
          "id": "C3",
          "type": "GRACE_PERIOD",
          "duration": "10 days",
          "duration_days": 10,
          "scope": [
            "R17"
          ],
          "description": "Ten-day cure period after at-risk notice"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R20",
      "type": "OBLIGATION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Pay earned amounts upon termination",
      "activation": "INACTIVE",
      "description": "Upon termination, Customer shall pay undisputed amounts earned before termination, less credits and offsets permitted by this Agreement.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T20",
          "type": "EVENT_TRIGGER",
          "condition": "Agreement is terminated",
          "reference_date": "termination_date"
        }
      ],
      "effects": [
        {
          "id": "E12",
          "type": "PAYMENT",
          "description": "Customer pays undisputed amounts earned before termination minus credits and offsets",
          "payment_formula": "earned_amount - credits - offsets",
          "payment_from": "Customer",
          "payment_to": "Bakery"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R23",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Maintain commercial general liability insurance",
      "activation": "INACTIVE",
      "description": "Bakery shall maintain commercial general liability insurance.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T23",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation throughout contract term",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R24",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Maintain commercial auto liability insurance",
      "activation": "INACTIVE",
      "description": "Bakery shall maintain commercial auto liability insurance.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T24",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation throughout contract term",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R25",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Maintain cargo or spoilage coverage",
      "activation": "INACTIVE",
      "description": "Bakery shall maintain any cargo or spoilage coverage reasonably appropriate for refrigerated food delivery.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T25",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation throughout contract term",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R27",
      "type": "OBLIGATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Use confidential information only to perform Agreement",
      "activation": "INACTIVE",
      "description": "Customer pricing, location volume, route information, and promotional plans are confidential. Bakery shall use such information only to perform this Agreement.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T27",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation throughout contract term and after termination",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R28",
      "type": "PROHIBITION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Use confidential information except for Agreement performance",
      "activation": "INACTIVE",
      "description": "Bakery must not use confidential information except to perform this Agreement.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T28",
          "type": "EVENT_TRIGGER",
          "condition": "Bakery receives or accesses confidential information"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R33",
      "type": "PROHIBITION",
      "party": "Either Party",
      "counterparty": "Other Party",
      "action": "Assign Agreement without consent",
      "activation": "INACTIVE",
      "description": "Neither party may assign this Agreement without the other party's consent except in connection with a sale of substantially all assets or a merger.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T33",
          "type": "EVENT_TRIGGER",
          "condition": "Party seeks to assign Agreement"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": [
        "R34"
      ]
    }
  ],
  "unmappable_rules": [
    {
      "id": "R2",
      "type": "WARRANTY",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Maintain product quality standards",
      "activation": "INACTIVE",
      "description": "Products shall be fresh, merchantable, properly packaged, and prepared in compliance with applicable food-safety requirements.",
      "mappable": false,
      "unmappable_reason": "WARRANTY is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T2",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuous obligation throughout contract performance",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R4",
      "type": "PERMISSION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Make emergency substitutions",
      "activation": "INACTIVE",
      "description": "Bakery may make emergency substitutions that are commercially reasonable and comparable in quality without Customer's consent.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T4",
          "type": "EVENT_TRIGGER",
          "condition": "Emergency situation requiring substitution"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R6",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Waive late delivery",
      "activation": "INACTIVE",
      "description": "A delivery after 7:00 a.m. is late unless Customer waives the delay in writing.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T6",
          "type": "EVENT_TRIGGER",
          "condition": "Delivery occurs after 7:00 a.m."
        }
      ],
      "effects": [
        {
          "id": "E2",
          "type": "RULE_ACTIVATION",
          "description": "Written waiver prevents delivery from being considered late",
          "target_rule_id": "R5",
          "new_state": "DELIVERY_COMPLIANT"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R8",
      "type": "IMMUNITY",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Excuses for late delivery do not apply",
      "activation": "INACTIVE",
      "description": "Vehicle unavailability, supplier issues, staffing shortfalls, traffic, or insurance delays do not excuse late delivery unless Customer gives a written waiver.",
      "mappable": false,
      "unmappable_reason": "IMMUNITY is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T8",
          "type": "EVENT_TRIGGER",
          "condition": "Operational issues cause late delivery"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": [
        "R6"
      ]
    },
    {
      "id": "R12",
      "type": "PERMISSION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Dispute invoice items",
      "activation": "INACTIVE",
      "description": "Customer may dispute an invoice item in good faith by written notice. Undisputed amounts remain payable.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T12",
          "type": "EVENT_TRIGGER",
          "condition": "Customer identifies disputed invoice item"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R14",
      "type": "PERMISSION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Apply credits or pay directly",
      "activation": "INACTIVE",
      "description": "Credits may be applied against the next invoice or paid by Bakery if no further invoice will be issued.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T14",
          "type": "EVENT_TRIGGER",
          "condition": "Late delivery credit is owed"
        }
      ],
      "effects": [
        {
          "id": "E7",
          "type": "PAYMENT",
          "description": "Credit applied to next invoice or paid directly",
          "payment_formula": "late_delivery_credits",
          "payment_from": "Bakery",
          "payment_to": "Customer"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R15",
      "type": "REPRESENTATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Late-delivery credit does not waive rights",
      "activation": "INACTIVE",
      "description": "A late-delivery credit is a price adjustment and does not waive Customer's termination rights or other remedies.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T15",
          "type": "EVENT_TRIGGER",
          "condition": "Late delivery credit is applied"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R16",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Place account at-risk",
      "activation": "INACTIVE",
      "description": "If Bakery has three late or missed deliveries in a rolling calendar month, Customer may place the account at-risk by written notice.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T16",
          "type": "THRESHOLD_TRIGGER",
          "condition": "Three late or missed deliveries in rolling calendar month",
          "duration": "rolling calendar month",
          "duration_days": 30,
          "threshold_field": "late_or_missed_deliveries",
          "threshold_value": "3",
          "threshold_operator": "gte"
        }
      ],
      "effects": [
        {
          "id": "E8",
          "type": "STATE_TRANSITION",
          "description": "Account transitions to at-risk status",
          "target_rule_id": "R17",
          "new_state": "AT_RISK"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R18",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Terminate for failure to cure",
      "activation": "INACTIVE",
      "description": "Customer may terminate this Agreement if Bakery fails to cure within the cure period.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T18",
          "type": "CONDITION_SUBSEQUENT",
          "condition": "Bakery fails to cure within 10-day cure period",
          "reference_date": "at_risk_notice_date",
          "duration": "10 days",
          "duration_days": 10
        }
      ],
      "effects": [
        {
          "id": "E10",
          "type": "TERMINATION",
          "description": "Customer may terminate Agreement",
          "new_state": "TERMINATED"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R19",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Terminate immediately after third miss",
      "activation": "INACTIVE",
      "description": "Customer may elect immediate termination after the third miss in a rolling calendar month.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T19",
          "type": "THRESHOLD_TRIGGER",
          "condition": "Third missed delivery in rolling calendar month",
          "duration": "rolling calendar month",
          "duration_days": 30,
          "threshold_field": "missed_deliveries",
          "threshold_value": "3",
          "threshold_operator": "gte"
        }
      ],
      "effects": [
        {
          "id": "E11",
          "type": "TERMINATION",
          "description": "Customer may immediately terminate Agreement",
          "new_state": "TERMINATED"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R21",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Reject nonconforming products",
      "activation": "INACTIVE",
      "description": "Customer may reject products that are materially nonconforming, unsafe, damaged, late, improperly packaged, or delivered outside agreed temperature or freshness requirements.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T21",
          "type": "EVENT_TRIGGER",
          "condition": "Products are materially nonconforming, unsafe, damaged, late, improperly packaged, or outside temperature/freshness requirements"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R22",
      "type": "REPRESENTATION",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Rejection does not limit late-delivery credit",
      "activation": "INACTIVE",
      "description": "Rejection of nonconforming products does not limit the late-delivery credit if the delivery was late.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T22",
          "type": "EVENT_TRIGGER",
          "condition": "Customer rejects products and delivery was late"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R26",
      "type": "PERMISSION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Request certificates of insurance",
      "activation": "INACTIVE",
      "description": "Customer may request certificates of insurance.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T26",
          "type": "EVENT_TRIGGER",
          "condition": "Customer determines need to verify insurance coverage"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R29",
      "type": "POWER",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Waive isolated misses, late deliveries, or shortages",
      "activation": "INACTIVE",
      "description": "Customer may waive isolated misses, late deliveries, or shortages in writing.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T29",
          "type": "EVENT_TRIGGER",
          "condition": "Isolated miss, late delivery, or shortage occurs"
        }
      ],
      "effects": [
        {
          "id": "E13",
          "type": "RULE_ACTIVATION",
          "description": "Written waiver prevents event from triggering consequences"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R30",
      "type": "REPRESENTATION",
      "party": "Customer",
      "counterparty": "Bakery",
      "action": "Waiver does not modify Agreement",
      "activation": "INACTIVE",
      "description": "A waiver for one event does not waive future events or modify the Agreement.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T30",
          "type": "EVENT_TRIGGER",
          "condition": "Customer provides written waiver"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R31",
      "type": "COVENANT",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Continue performing deliveries",
      "activation": "INACTIVE",
      "description": "This Agreement begins on the effective date and continues month to month unless terminated under Section 6 or by either party on thirty days' written notice after the first three months.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T31",
          "type": "DATE_TRIGGER",
          "condition": "Agreement becomes effective",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": [
        "R32",
        "R18",
        "R19"
      ]
    },
    {
      "id": "R32",
      "type": "POWER",
      "party": "Either Party",
      "counterparty": "Other Party",
      "action": "Terminate on 30 days' notice after first three months",
      "activation": "INACTIVE",
      "description": "Either party may terminate on thirty days' written notice after the first three months.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T32",
          "type": "DATE_TRIGGER",
          "condition": "First three months have elapsed",
          "reference_date": "effective_date",
          "duration": "90 days",
          "duration_days": 90
        }
      ],
      "effects": [
        {
          "id": "E14",
          "type": "TERMINATION",
          "description": "Agreement terminates 30 days after written notice",
          "new_state": "TERMINATED"
        }
      ],
      "constraints": [
        {
          "id": "C4",
          "type": "GRACE_PERIOD",
          "duration": "30 days",
          "duration_days": 30,
          "scope": [
            "R32"
          ],
          "description": "30-day notice period before termination becomes effective"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R34",
      "type": "PERMISSION",
      "party": "Either Party",
      "counterparty": "Other Party",
      "action": "Assign in connection with asset sale or merger",
      "activation": "INACTIVE",
      "description": "Either party may assign in connection with a sale of substantially all assets or a merger without the other party's consent.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T34",
          "type": "EVENT_TRIGGER",
          "condition": "Sale of substantially all assets or merger occurs"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R35",
      "type": "POWER",
      "party": "Either Party",
      "counterparty": "Other Party",
      "action": "Amend Agreement",
      "activation": "INACTIVE",
      "description": "This Agreement may be amended only in writing.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T35",
          "type": "EVENT_TRIGGER",
          "condition": "Parties agree to amend Agreement"
        }
      ],
      "effects": [
        {
          "id": "E15",
          "type": "RETROACTIVE_REVISION",
          "description": "Written amendment modifies Agreement terms"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R36",
      "type": "POWER",
      "party": "Bakery",
      "counterparty": "Customer",
      "action": "Adjust route start date",
      "activation": "INACTIVE",
      "description": "The parties may adjust the start date only by written agreement.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T36",
          "type": "EVENT_TRIGGER",
          "condition": "Parties agree to adjust route start date"
        }
      ],
      "effects": [
        {
          "id": "E16",
          "type": "RETROACTIVE_REVISION",
          "description": "Route start date is modified by written agreement"
        }
      ],
      "constraints": [],
      "exceptions": []
    }
  ]
}
```

---

- 2026-05-16: Ingested from DDKT Maria's Bakery output JSON for scenario optimization and deterministic FSM verification.
