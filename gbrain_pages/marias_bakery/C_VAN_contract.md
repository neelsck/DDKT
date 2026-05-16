---
type: contract-fsm
title: "Maria's Bakery - C VAN contract"
tags: [marias-bakery, contract-fsm, executable-contract, fsm]
contract_id: C_VAN_contract
source_file: output/C_VAN_contract/fsm.json
---

# Maria's Bakery - C VAN contract

This page ingests the finite state machine JSON for `C_VAN_contract`. The app uses this as contract-grounded retrieval context, then verifies proposed scenarios by replaying events through the FSM.

## Contract Facts

- Parties: Maria's Bakery LLC, ColdRoad Vans Inc., Neighborhood Bank, N.A.
- Initial state: `ACTIVE`
- State count: 8
- Transition count: 10
- Amounts: {"down_payment": "8000", "financed_amount": "50000", "monthly_payment": "1175", "purchase_price": "58000"}
- Thresholds: {"bakery_business_use_percentage_minimum": "50"}

## States

| State | Terminal | Description |
|---|---:|---|
| `ACTIVE` | False | Contract signed, down payment due, awaiting delivery |
| `AWAITING_DELIVERY` | False | Down payment made, equipment ownership transferred, awaiting physical delivery |
| `DELIVERY_GRACE` | False | Scheduled delivery date passed, within 5-day grace period |
| `DELIVERED_UNINSURED` | False | Equipment delivered but commercial insurance not yet active, no commercial use allowed |
| `DELIVERED_INSURED` | False | Equipment delivered and insured, inspection period, ready for commercial use |
| `OPERATIONAL` | False | Equipment inspected and accepted, monthly payments active, operational obligations ongoing |
| `FULFILLED` | True | All installments paid, contract obligations completed |
| `TERMINATED` | True | Contract terminated due to breach or other termination event |

## Transitions

| Transition | Event | From | To | Guard | Effects |
|---|---|---|---|---|---|
| TR1 | `down_payment_made` | `ACTIVE` | `AWAITING_DELIVERY` |  | PAYMENT: Down payment of $8,000 transferred at signing; ASSET_TRANSFER: Equipment ownership transferred from Dealer to Buyer (R1) |
| TR2 | `scheduled_delivery_date_passed` | `AWAITING_DELIVERY` | `DELIVERY_GRACE` |  |  |
| TR3 | `equipment_delivered` | `AWAITING_DELIVERY`, `DELIVERY_GRACE` | `DELIVERED_UNINSURED` | `insurance_active == False` | ASSET_TRANSFER: Physical delivery of Equipment with complete delivery package to designated location (R4, R5) |
| TR4 | `equipment_delivered` | `AWAITING_DELIVERY`, `DELIVERY_GRACE` | `DELIVERED_INSURED` | `insurance_active == True` | ASSET_TRANSFER: Physical delivery of Equipment with complete delivery package to designated location (R4, R5) |
| TR5 | `insurance_activated` | `DELIVERED_UNINSURED` | `DELIVERED_INSURED` |  |  |
| TR6 | `equipment_inspected_accepted` | `DELIVERED_INSURED` | `OPERATIONAL` |  |  |
| TR7 | `equipment_inspected_rejected` | `DELIVERED_INSURED` | `TERMINATED` |  | FORFEITURE: Buyer rejects equipment on inspection, contract may terminate per rejection terms |
| TR8 | `monthly_payment_made` | `OPERATIONAL` | `OPERATIONAL` |  | PAYMENT: Monthly installment payment of $1,175 to Lender (R23) |
| TR9 | `final_payment_made` | `OPERATIONAL` | `FULFILLED` |  | PAYMENT: Final monthly installment payment completing financing obligation |
| TR10 | `contract_terminated` | `ACTIVE`, `AWAITING_DELIVERY`, `DELIVERY_GRACE`, `DELIVERED_UNINSURED`, `DELIVERED_INSURED`, `OPERATIONAL` | `TERMINATED` |  | FORFEITURE: Contract terminated due to breach, default, or other termination event |

## Original Contract Text

```text
REFRIGERATED VEHICLE PURCHASE, SECURITY, AND INSURANCE AGREEMENT

This Refrigerated Vehicle Purchase, Security, and Insurance Agreement (this
"Agreement") is entered into as of December 20, 2026, by and among Maria's
Bakery LLC, a California limited liability company ("Buyer"), ColdRoad Vans
Inc., a California corporation ("Dealer"), and Neighborhood Bank, N.A.
("Lender").

1. PURCHASE OF EQUIPMENT

1.1 Equipment. Dealer agrees to sell, and Buyer agrees to purchase, one
2026 refrigerated delivery van with an integrated refrigeration unit, cargo
temperature display, insulation package, rear shelving, and related manuals
(collectively, the "Equipment").

1.2 Purchase Price. The purchase price for the Equipment is $58,000.00.
Buyer shall pay $8,000.00 as a down payment at signing. The remaining amount
shall be financed by Lender on the terms of this Agreement and the payment
schedule executed by Buyer.

1.3 Delivery Package. Delivery is complete only when Dealer tenders the
vehicle, keys, registration documents, refrigeration-unit operating manual,
warranty documents, and a delivery acceptance certificate.

2. DELIVERY

2.1 Delivery Obligation. Dealer shall deliver the Equipment to Buyer at the
Premises or another mutually agreed location.

2.2 Grace Period. Dealer has a five-day grace period after the scheduled
delivery date. Delivery after the grace period is a Dealer delay, but delay
does not excuse Buyer from payment obligations once Buyer accepts delivery.

2.3 Inspection. Buyer shall inspect the Equipment on delivery. Acceptance
does not waive latent defects or warranty claims.

3. SECURITY INTEREST

3.1 Grant of Security Interest. To secure prompt payment and performance of
all obligations owing to Lender, Buyer grants Lender a first-priority security
interest in the Equipment, all additions, attachments, accessories,
substitutions, replacement parts, insurance proceeds, and records related to
the Equipment.

3.2 Filings. Buyer authorizes Lender to file financing statements and other
records necessary or advisable to perfect Lender's security interest.

3.3 No Liens. Buyer shall keep the Equipment free from liens other than
Lender's security interest and permitted statutory liens arising in the
ordinary course and discharged before delinquency.

4. INSURANCE CONDITION

4.1 Commercial Insurance Required. Buyer shall not use the Equipment for
commercial delivery unless commercial auto liability insurance and a
refrigerated cargo or spoilage endorsement are active.

4.2 Evidence of Insurance. Buyer shall provide Lender and Dealer with
evidence of insurance before commercial use. Policies shall name Lender as
loss payee for physical damage coverage.

4.3 No Use Before Binder. If the Equipment is delivered before the commercial
insurance binder is active, Buyer shall hold the Equipment in a
delivered-but-uninsured status and shall not use it for customer deliveries.

5. PLACED-IN-SERVICE CONDITION

5.1 Operational Condition. Buyer may designate the Equipment as placed in
business delivery service only after all of the following are true:
(a) Dealer has delivered the Equipment;
(b) commercial insurance is active;
(c) the Equipment is available for regular bakery delivery use; and
(d) more than 50% of its expected use is bakery business use.

5.2 No Tax Determination. This Agreement records operational facts only.
Neither Dealer nor Lender gives tax advice or determines Buyer's eligibility
for any deduction, credit, depreciation, or expensing treatment.

6. PAYMENTS

6.1 Monthly Payment. Buyer shall pay Lender $1,175.00 per month beginning
after delivery of the Equipment.

6.2 Application of Payments. Payments may be applied to fees, interest,
principal, protective advances, and enforcement costs in the order permitted
by the financing documents and applicable law.

6.3 No Setoff. Buyer shall make payments without setoff against Lender,
except to the extent non-waivable law provides otherwise.

7. MAINTENANCE AND USE

7.1 Maintenance. Buyer shall maintain the Equipment in good working order,
keep the refrigeration unit serviced, preserve maintenance records, and use
the Equipment in compliance with law, insurance requirements, and manufacturer
instructions.

7.2 Location. Buyer shall keep the Equipment at Buyer's business location or
in ordinary delivery operations unless Lender consents to another primary
location.

7.3 Risk of Loss. Risk of loss passes to Buyer on delivery acceptance. Loss,
damage, theft, or interruption of use does not excuse Buyer's payment
obligations.

8. EVENTS OF DEFAULT

Each of the following is an event of default:
(a) Buyer fails to pay an amount when due;
(b) Buyer uses the Equipment commercially before required insurance is active;
(c) Buyer grants or permits an unauthorized lien;
(d) Buyer materially misrepresents the Equipment's use, location, or insurance;
or
(e) Buyer fails to maintain or protect the Equipment.

9. REMEDIES

Upon default, Lender may accelerate unpaid amounts, require immediate payment,
take possession of the Equipment as permitted by law, enforce its security
interest, apply insurance proceeds, and recover reasonable enforcement costs.
Dealer may suspend any open warranty service to the extent permitted by law if
Buyer has failed to pay amounts owed to Dealer.

10. WARRANTIES

Dealer assigns to Buyer available manufacturer warranties for the vehicle and
refrigeration unit. Dealer gives no warranty beyond the express written
warranties delivered with the Equipment.

11. MISCELLANEOUS

This Agreement binds the parties and their permitted successors. Amendments
must be in writing. Electronic signatures are effective. California law governs
except to the extent federal law applies to Lender.

BUYER:
Maria's Bakery LLC

DEALER:
ColdRoad Vans Inc.

LENDER:
Neighborhood Bank, N.A.
```

## Raw FSM JSON

```json
{
  "contract_id": "C_VAN_contract",
  "parties": [
    "Maria's Bakery LLC",
    "ColdRoad Vans Inc.",
    "Neighborhood Bank, N.A."
  ],
  "initial_state": "ACTIVE",
  "params": {
    "parties": [
      "Maria's Bakery LLC",
      "ColdRoad Vans Inc.",
      "Neighborhood Bank, N.A."
    ],
    "base_dates": {
      "effective_date": "2026-12-20",
      "scheduled_delivery_date": null,
      "delivery_date": null
    },
    "amounts": {
      "purchase_price": "58000",
      "down_payment": "8000",
      "financed_amount": "50000",
      "monthly_payment": "1175"
    },
    "rates": {},
    "durations": {
      "delivery_grace_period_days": 5
    },
    "thresholds": {
      "bakery_business_use_percentage_minimum": "50"
    }
  },
  "states": [
    {
      "id": "ACTIVE",
      "description": "Contract signed, down payment due, awaiting delivery",
      "terminal": false,
      "active_rule_ids": [
        "R1",
        "R2",
        "R3",
        "R10",
        "R12"
      ]
    },
    {
      "id": "AWAITING_DELIVERY",
      "description": "Down payment made, equipment ownership transferred, awaiting physical delivery",
      "terminal": false,
      "active_rule_ids": [
        "R4",
        "R5",
        "R12"
      ]
    },
    {
      "id": "DELIVERY_GRACE",
      "description": "Scheduled delivery date passed, within 5-day grace period",
      "terminal": false,
      "active_rule_ids": [
        "R4",
        "R5",
        "R12"
      ]
    },
    {
      "id": "DELIVERED_UNINSURED",
      "description": "Equipment delivered but commercial insurance not yet active, no commercial use allowed",
      "terminal": false,
      "active_rule_ids": [
        "R8",
        "R12",
        "R13",
        "R14",
        "R15",
        "R16",
        "R17",
        "R18",
        "R19"
      ]
    },
    {
      "id": "DELIVERED_INSURED",
      "description": "Equipment delivered and insured, inspection period, ready for commercial use",
      "terminal": false,
      "active_rule_ids": [
        "R8",
        "R12",
        "R15",
        "R16",
        "R17",
        "R23",
        "R25",
        "R26",
        "R27",
        "R28",
        "R29",
        "R30"
      ]
    },
    {
      "id": "OPERATIONAL",
      "description": "Equipment inspected and accepted, monthly payments active, operational obligations ongoing",
      "terminal": false,
      "active_rule_ids": [
        "R12",
        "R23",
        "R25",
        "R26",
        "R27",
        "R28",
        "R29",
        "R30"
      ]
    },
    {
      "id": "FULFILLED",
      "description": "All installments paid, contract obligations completed",
      "terminal": true,
      "active_rule_ids": []
    },
    {
      "id": "TERMINATED",
      "description": "Contract terminated due to breach or other termination event",
      "terminal": true,
      "active_rule_ids": []
    }
  ],
  "transitions": [
    {
      "id": "TR1",
      "from_states": [
        "ACTIVE"
      ],
      "to_state": "AWAITING_DELIVERY",
      "event_type": "down_payment_made",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "down_payment",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "ColdRoad Vans Inc.",
          "cap": null,
          "description": "Down payment of $8,000 transferred at signing"
        },
        {
          "id": "E2",
          "type": "ASSET_TRANSFER",
          "description": "Equipment ownership transferred from Dealer to Buyer (R1)"
        }
      ],
      "description": "Buyer makes down payment and receives equipment ownership"
    },
    {
      "id": "TR2",
      "from_states": [
        "AWAITING_DELIVERY"
      ],
      "to_state": "DELIVERY_GRACE",
      "event_type": "scheduled_delivery_date_passed",
      "guard": null,
      "effects": [],
      "description": "Scheduled delivery date passes, entering 5-day grace period"
    },
    {
      "id": "TR3",
      "from_states": [
        "AWAITING_DELIVERY",
        "DELIVERY_GRACE"
      ],
      "to_state": "DELIVERED_UNINSURED",
      "event_type": "equipment_delivered",
      "guard": "insurance_active == False",
      "effects": [
        {
          "id": "E1",
          "type": "ASSET_TRANSFER",
          "description": "Physical delivery of Equipment with complete delivery package to designated location (R4, R5)"
        }
      ],
      "description": "Equipment delivered but insurance not yet active"
    },
    {
      "id": "TR4",
      "from_states": [
        "AWAITING_DELIVERY",
        "DELIVERY_GRACE"
      ],
      "to_state": "DELIVERED_INSURED",
      "event_type": "equipment_delivered",
      "guard": "insurance_active == True",
      "effects": [
        {
          "id": "E1",
          "type": "ASSET_TRANSFER",
          "description": "Physical delivery of Equipment with complete delivery package to designated location (R4, R5)"
        }
      ],
      "description": "Equipment delivered with insurance already active"
    },
    {
      "id": "TR5",
      "from_states": [
        "DELIVERED_UNINSURED"
      ],
      "to_state": "DELIVERED_INSURED",
      "event_type": "insurance_activated",
      "guard": null,
      "effects": [],
      "description": "Commercial insurance binder becomes active, equipment ready for commercial use"
    },
    {
      "id": "TR6",
      "from_states": [
        "DELIVERED_INSURED"
      ],
      "to_state": "OPERATIONAL",
      "event_type": "equipment_inspected_accepted",
      "guard": null,
      "effects": [],
      "description": "Buyer inspects and accepts equipment, operational phase begins"
    },
    {
      "id": "TR7",
      "from_states": [
        "DELIVERED_INSURED"
      ],
      "to_state": "TERMINATED",
      "event_type": "equipment_inspected_rejected",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "FORFEITURE",
          "description": "Buyer rejects equipment on inspection, contract may terminate per rejection terms"
        }
      ],
      "description": "Buyer inspects and rejects equipment"
    },
    {
      "id": "TR8",
      "from_states": [
        "OPERATIONAL"
      ],
      "to_state": "OPERATIONAL",
      "event_type": "monthly_payment_made",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "monthly_payment",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "Neighborhood Bank, N.A.",
          "cap": null,
          "description": "Monthly installment payment of $1,175 to Lender (R23)"
        }
      ],
      "description": "Buyer makes monthly installment payment"
    },
    {
      "id": "TR9",
      "from_states": [
        "OPERATIONAL"
      ],
      "to_state": "FULFILLED",
      "event_type": "final_payment_made",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "PAYMENT",
          "payment_formula": "monthly_payment",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "Neighborhood Bank, N.A.",
          "cap": null,
          "description": "Final monthly installment payment completing financing obligation"
        }
      ],
      "description": "Buyer makes final payment, all obligations fulfilled"
    },
    {
      "id": "TR10",
      "from_states": [
        "ACTIVE",
        "AWAITING_DELIVERY",
        "DELIVERY_GRACE",
        "DELIVERED_UNINSURED",
        "DELIVERED_INSURED",
        "OPERATIONAL"
      ],
      "to_state": "TERMINATED",
      "event_type": "contract_terminated",
      "guard": null,
      "effects": [
        {
          "id": "E1",
          "type": "FORFEITURE",
          "description": "Contract terminated due to breach, default, or other termination event"
        }
      ],
      "description": "Contract terminates due to breach or other termination condition"
    }
  ],
  "rules": [
    {
      "id": "R1",
      "type": "OBLIGATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Sell Equipment to Buyer",
      "activation": "INACTIVE",
      "description": "Dealer agrees to sell, and Buyer agrees to purchase, one 2026 refrigerated delivery van with an integrated refrigeration unit, cargo temperature display, insulation package, rear shelving, and related manuals (collectively, the 'Equipment').",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T1",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [
        {
          "id": "E1",
          "type": "ASSET_TRANSFER",
          "description": "Transfer of Equipment ownership from Dealer to Buyer"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R2",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Purchase Equipment from Dealer",
      "activation": "INACTIVE",
      "description": "Dealer agrees to sell, and Buyer agrees to purchase, one 2026 refrigerated delivery van with an integrated refrigeration unit, cargo temperature display, insulation package, rear shelving, and related manuals (collectively, the 'Equipment').",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T2",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [
        {
          "id": "E2",
          "type": "RULE_ACTIVATION",
          "description": "Activates payment obligations",
          "target_rule_id": "R3"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R3",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Pay down payment at signing",
      "activation": "INACTIVE",
      "description": "Buyer shall pay $8,000.00 as a down payment at signing.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T3",
          "type": "DATE_TRIGGER",
          "condition": "At signing of Agreement",
          "reference_date": "effective_date",
          "duration_days": 0
        }
      ],
      "effects": [
        {
          "id": "E3",
          "type": "PAYMENT",
          "description": "Transfer of $8,000.00 down payment",
          "payment_formula": "8000",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "ColdRoad Vans Inc.",
          "cap": "8000"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R4",
      "type": "OBLIGATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Deliver Equipment with complete delivery package",
      "activation": "INACTIVE",
      "description": "Delivery is complete only when Dealer tenders the vehicle, keys, registration documents, refrigeration-unit operating manual, warranty documents, and a delivery acceptance certificate.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T4",
          "type": "DATE_TRIGGER",
          "condition": "Scheduled delivery date",
          "reference_date": "scheduled_delivery_date"
        }
      ],
      "effects": [
        {
          "id": "E4",
          "type": "ASSET_TRANSFER",
          "description": "Physical delivery of Equipment and all required documents to Buyer",
          "new_state": "delivered"
        },
        {
          "id": "E4b",
          "type": "RULE_ACTIVATION",
          "description": "Activates risk of loss transfer and inspection obligation",
          "target_rule_id": "R33"
        }
      ],
      "constraints": [
        {
          "id": "C1",
          "type": "GRACE_PERIOD",
          "duration": "5 days",
          "duration_days": 5,
          "scope": [
            "R4"
          ],
          "description": "Dealer has a five-day grace period after the scheduled delivery date before delay occurs"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R5",
      "type": "OBLIGATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Deliver Equipment to Premises or mutually agreed location",
      "activation": "INACTIVE",
      "description": "Dealer shall deliver the Equipment to Buyer at the Premises or another mutually agreed location.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T5",
          "type": "DATE_TRIGGER",
          "condition": "Scheduled delivery date",
          "reference_date": "scheduled_delivery_date"
        }
      ],
      "effects": [
        {
          "id": "E5",
          "type": "ASSET_TRANSFER",
          "description": "Physical delivery of Equipment to designated location"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R8",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Inspect Equipment on delivery",
      "activation": "INACTIVE",
      "description": "Buyer shall inspect the Equipment on delivery.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T8",
          "type": "EVENT_TRIGGER",
          "condition": "Delivery of Equipment occurs"
        }
      ],
      "effects": [
        {
          "id": "E8",
          "type": "STATE_TRANSITION",
          "description": "Inspection performed, Equipment accepted or rejected",
          "new_state": "inspected"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R10",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Grant first-priority security interest in Equipment",
      "activation": "INACTIVE",
      "description": "To secure prompt payment and performance of all obligations owing to Lender, Buyer grants Lender a first-priority security interest in the Equipment, all additions, attachments, accessories, substitutions, replacement parts, insurance proceeds, and records related to the Equipment.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T10",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [
        {
          "id": "E10",
          "type": "STATE_TRANSITION",
          "description": "Security interest granted to Lender in Equipment and related property",
          "new_state": "secured"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R12",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Keep Equipment free from unauthorized liens",
      "activation": "INACTIVE",
      "description": "Buyer shall keep the Equipment free from liens other than Lender's security interest and permitted statutory liens arising in the ordinary course and discharged before delinquency.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T12",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [
        {
          "id": "C2",
          "type": "CARVE_OUT",
          "scope": [
            "R12"
          ],
          "description": "Permitted statutory liens arising in ordinary course and discharged before delinquency are allowed"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R13",
      "type": "PROHIBITION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Do not use Equipment for commercial delivery without active commercial auto liability insurance",
      "activation": "INACTIVE",
      "description": "Buyer shall not use the Equipment for commercial delivery unless commercial auto liability insurance and a refrigerated cargo or spoilage endorsement are active.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T13",
          "type": "CONDITION_PRECEDENT",
          "condition": "Commercial auto liability insurance is not active",
          "threshold_field": "commercial_insurance_active",
          "threshold_value": "false",
          "threshold_operator": "eq"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R14",
      "type": "PROHIBITION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Do not use Equipment for commercial delivery without refrigerated cargo or spoilage endorsement",
      "activation": "INACTIVE",
      "description": "Buyer shall not use the Equipment for commercial delivery unless commercial auto liability insurance and a refrigerated cargo or spoilage endorsement are active.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T14",
          "type": "CONDITION_PRECEDENT",
          "condition": "Refrigerated cargo or spoilage endorsement is not active",
          "threshold_field": "cargo_endorsement_active",
          "threshold_value": "false",
          "threshold_operator": "eq"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R15",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Provide Lender with evidence of insurance before commercial use",
      "activation": "INACTIVE",
      "description": "Buyer shall provide Lender and Dealer with evidence of insurance before commercial use.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T15",
          "type": "CONDITION_PRECEDENT",
          "condition": "Before commercial use of Equipment begins"
        }
      ],
      "effects": [
        {
          "id": "E15",
          "type": "STATE_TRANSITION",
          "description": "Lender receives and verifies insurance documentation",
          "new_state": "insurance_verified"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R16",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Provide Dealer with evidence of insurance before commercial use",
      "activation": "INACTIVE",
      "description": "Buyer shall provide Lender and Dealer with evidence of insurance before commercial use.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T16",
          "type": "CONDITION_PRECEDENT",
          "condition": "Before commercial use of Equipment begins"
        }
      ],
      "effects": [
        {
          "id": "E16",
          "type": "STATE_TRANSITION",
          "description": "Dealer receives and verifies insurance documentation",
          "new_state": "insurance_verified_dealer"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R17",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Name Lender as loss payee for physical damage coverage",
      "activation": "INACTIVE",
      "description": "Policies shall name Lender as loss payee for physical damage coverage.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T17",
          "type": "CONDITION_PRECEDENT",
          "condition": "Before obtaining commercial insurance"
        }
      ],
      "effects": [
        {
          "id": "E17",
          "type": "STATE_TRANSITION",
          "description": "Insurance policy designates Lender as loss payee",
          "new_state": "loss_payee_designated"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R18",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Hold Equipment in delivered-but-uninsured status if delivered before insurance active",
      "activation": "INACTIVE",
      "description": "If the Equipment is delivered before the commercial insurance binder is active, Buyer shall hold the Equipment in a delivered-but-uninsured status and shall not use it for customer deliveries.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T18",
          "type": "CONDITION_PRECEDENT",
          "condition": "Equipment is delivered AND commercial insurance binder is not active",
          "threshold_field": "insurance_binder_active",
          "threshold_value": "false",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E18",
          "type": "STATE_TRANSITION",
          "description": "Equipment enters delivered-but-uninsured status",
          "new_state": "delivered_uninsured"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R19",
      "type": "PROHIBITION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Do not use Equipment for customer deliveries if delivered before insurance active",
      "activation": "INACTIVE",
      "description": "If the Equipment is delivered before the commercial insurance binder is active, Buyer shall hold the Equipment in a delivered-but-uninsured status and shall not use it for customer deliveries.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T19",
          "type": "CONDITION_PRECEDENT",
          "condition": "Equipment is in delivered-but-uninsured status",
          "threshold_field": "equipment_status",
          "threshold_value": "delivered_uninsured",
          "threshold_operator": "eq"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R23",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Pay monthly installment to Lender",
      "activation": "INACTIVE",
      "description": "Buyer shall pay Lender $1,175.00 per month beginning after delivery of the Equipment.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T23",
          "type": "EVENT_TRIGGER",
          "condition": "After delivery of Equipment, monthly",
          "reference_date": "delivery_date",
          "duration": "1 month",
          "duration_days": 30
        }
      ],
      "effects": [
        {
          "id": "E23",
          "type": "PAYMENT",
          "description": "Monthly payment of $1,175.00 from Buyer to Lender",
          "payment_formula": "1175",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "Neighborhood Bank, N.A."
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R25",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Make payments without setoff against Lender",
      "activation": "INACTIVE",
      "description": "Buyer shall make payments without setoff against Lender, except to the extent non-waivable law provides otherwise.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T25",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Each payment due date"
        }
      ],
      "effects": [],
      "constraints": [
        {
          "id": "C4",
          "type": "CARVE_OUT",
          "scope": [
            "R25"
          ],
          "description": "Exception where non-waivable law permits setoff"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R26",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Maintain Equipment in good working order",
      "activation": "INACTIVE",
      "description": "Buyer shall maintain the Equipment in good working order, keep the refrigeration unit serviced, preserve maintenance records, and use the Equipment in compliance with law, insurance requirements, and manufacturer instructions.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T26",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from delivery",
          "reference_date": "delivery_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R27",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Keep refrigeration unit serviced",
      "activation": "INACTIVE",
      "description": "Buyer shall maintain the Equipment in good working order, keep the refrigeration unit serviced, preserve maintenance records, and use the Equipment in compliance with law, insurance requirements, and manufacturer instructions.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T27",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from delivery",
          "reference_date": "delivery_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R28",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Preserve maintenance records",
      "activation": "INACTIVE",
      "description": "Buyer shall maintain the Equipment in good working order, keep the refrigeration unit serviced, preserve maintenance records, and use the Equipment in compliance with law, insurance requirements, and manufacturer instructions.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T28",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from delivery",
          "reference_date": "delivery_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R29",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Use Equipment in compliance with law, insurance requirements, and manufacturer instructions",
      "activation": "INACTIVE",
      "description": "Buyer shall maintain the Equipment in good working order, keep the refrigeration unit serviced, preserve maintenance records, and use the Equipment in compliance with law, insurance requirements, and manufacturer instructions.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T29",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from delivery",
          "reference_date": "delivery_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R30",
      "type": "OBLIGATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Keep Equipment at business location or in ordinary delivery operations",
      "activation": "INACTIVE",
      "description": "Buyer shall keep the Equipment at Buyer's business location or in ordinary delivery operations unless Lender consents to another primary location.",
      "mappable": true,
      "unmappable_reason": null,
      "triggers": [
        {
          "id": "T30",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Continuously from delivery",
          "reference_date": "delivery_date"
        }
      ],
      "effects": [],
      "constraints": [
        {
          "id": "C5",
          "type": "CARVE_OUT",
          "scope": [
            "R30"
          ],
          "description": "Lender may consent to another primary location"
        }
      ],
      "exceptions": []
    }
  ],
  "unmappable_rules": [
    {
      "id": "R6",
      "type": "REPRESENTATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Dealer delay determination",
      "activation": "INACTIVE",
      "description": "Delivery after the grace period is a Dealer delay, but delay does not excuse Buyer from payment obligations once Buyer accepts delivery.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T6",
          "type": "TEMPORAL_TRIGGER",
          "condition": "Delivery occurs more than 5 days after scheduled delivery date",
          "reference_date": "scheduled_delivery_date",
          "duration": "5 days",
          "duration_days": 5
        }
      ],
      "effects": [
        {
          "id": "E6",
          "type": "STATE_TRANSITION",
          "description": "Delivery is classified as delayed",
          "new_state": "dealer_delayed"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R7",
      "type": "IMMUNITY",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Payment obligations not excused by Dealer delay",
      "activation": "INACTIVE",
      "description": "Delay does not excuse Buyer from payment obligations once Buyer accepts delivery.",
      "mappable": false,
      "unmappable_reason": "IMMUNITY is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T7",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer accepts delivery after Dealer delay"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R9",
      "type": "IMMUNITY",
      "party": "Maria's Bakery LLC",
      "counterparty": "ColdRoad Vans Inc.",
      "action": "Acceptance does not waive latent defects or warranty claims",
      "activation": "INACTIVE",
      "description": "Acceptance does not waive latent defects or warranty claims.",
      "mappable": false,
      "unmappable_reason": "IMMUNITY is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T9",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer accepts delivery"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R11",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "File financing statements to perfect security interest",
      "activation": "INACTIVE",
      "description": "Buyer authorizes Lender to file financing statements and other records necessary or advisable to perfect Lender's security interest.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T11",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date or any time thereafter",
          "reference_date": "effective_date"
        }
      ],
      "effects": [
        {
          "id": "E11",
          "type": "STATE_TRANSITION",
          "description": "Lender may file UCC-1 and other perfection documents",
          "new_state": "perfected"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R20",
      "type": "PERMISSION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Designate Equipment as placed in business delivery service when conditions met",
      "activation": "INACTIVE",
      "description": "Buyer may designate the Equipment as placed in business delivery service only after all of the following are true: (a) Dealer has delivered the Equipment; (b) commercial insurance is active; (c) the Equipment is available for regular bakery delivery use; and (d) more than 50% of its expected use is bakery business use.",
      "mappable": false,
      "unmappable_reason": "PERMISSION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T20a",
          "type": "CONDITION_PRECEDENT",
          "condition": "Dealer has delivered the Equipment",
          "threshold_field": "equipment_delivered",
          "threshold_value": "true",
          "threshold_operator": "eq"
        },
        {
          "id": "T20b",
          "type": "CONDITION_PRECEDENT",
          "condition": "Commercial insurance is active",
          "threshold_field": "commercial_insurance_active",
          "threshold_value": "true",
          "threshold_operator": "eq"
        },
        {
          "id": "T20c",
          "type": "CONDITION_PRECEDENT",
          "condition": "Equipment is available for regular bakery delivery use",
          "threshold_field": "equipment_available",
          "threshold_value": "true",
          "threshold_operator": "eq"
        },
        {
          "id": "T20d",
          "type": "THRESHOLD_TRIGGER",
          "condition": "More than 50% of expected use is bakery business use",
          "threshold_field": "bakery_business_use_percentage",
          "threshold_value": "50",
          "threshold_operator": "gt"
        }
      ],
      "effects": [
        {
          "id": "E20",
          "type": "STATE_TRANSITION",
          "description": "Equipment designated as placed in service",
          "new_state": "placed_in_service"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R21",
      "type": "REPRESENTATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Dealer gives no tax advice",
      "activation": "INACTIVE",
      "description": "This Agreement records operational facts only. Neither Dealer nor Lender gives tax advice or determines Buyer's eligibility for any deduction, credit, depreciation, or expensing treatment.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T21",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R22",
      "type": "REPRESENTATION",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Lender gives no tax advice",
      "activation": "INACTIVE",
      "description": "This Agreement records operational facts only. Neither Dealer nor Lender gives tax advice or determines Buyer's eligibility for any deduction, credit, depreciation, or expensing treatment.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T22",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R24",
      "type": "COVENANT",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Apply payments in permitted order",
      "activation": "INACTIVE",
      "description": "Payments may be applied to fees, interest, principal, protective advances, and enforcement costs in the order permitted by the financing documents and applicable law.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T24",
          "type": "EVENT_TRIGGER",
          "condition": "Receipt of payment from Buyer"
        }
      ],
      "effects": [
        {
          "id": "E24",
          "type": "PAYMENT",
          "description": "Payment allocated to fees, interest, principal, protective advances, and enforcement costs"
        }
      ],
      "constraints": [
        {
          "id": "C3",
          "type": "CONTROLLING_ITEM",
          "scope": [
            "R24"
          ],
          "description": "Application order controlled by financing documents and applicable law"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R31",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Consent to alternative primary location for Equipment",
      "activation": "INACTIVE",
      "description": "Buyer shall keep the Equipment at Buyer's business location or in ordinary delivery operations unless Lender consents to another primary location.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T31",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer requests alternative location"
        }
      ],
      "effects": [
        {
          "id": "E31",
          "type": "STATE_TRANSITION",
          "description": "Alternative location approved by Lender",
          "new_state": "alternative_location_approved"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R32",
      "type": "COVENANT",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Risk of loss passes to Buyer on delivery acceptance",
      "activation": "INACTIVE",
      "description": "Risk of loss passes to Buyer on delivery acceptance.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T32",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer accepts delivery of Equipment"
        }
      ],
      "effects": [
        {
          "id": "E32",
          "type": "STATE_TRANSITION",
          "description": "Buyer bears risk of loss, damage, theft, or interruption",
          "new_state": "risk_transferred"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R33",
      "type": "IMMUNITY",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Loss, damage, theft, or interruption does not excuse payment obligations",
      "activation": "INACTIVE",
      "description": "Loss, damage, theft, or interruption of use does not excuse Buyer's payment obligations.",
      "mappable": false,
      "unmappable_reason": "IMMUNITY is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T33",
          "type": "EVENT_TRIGGER",
          "condition": "Loss, damage, theft, or interruption of Equipment occurs"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R34",
      "type": "REPRESENTATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Event of default: failure to pay when due",
      "activation": "INACTIVE",
      "description": "Each of the following is an event of default: (a) Buyer fails to pay an amount when due.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T34",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer fails to pay an amount when due"
        }
      ],
      "effects": [
        {
          "id": "E34",
          "type": "STATE_TRANSITION",
          "description": "Event of default declared",
          "new_state": "default"
        },
        {
          "id": "E34b",
          "type": "RULE_ACTIVATION",
          "description": "Activates default remedies",
          "target_rule_id": "R39"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R35",
      "type": "REPRESENTATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Event of default: commercial use before insurance active",
      "activation": "INACTIVE",
      "description": "Each of the following is an event of default: (b) Buyer uses the Equipment commercially before required insurance is active.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T35",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer uses Equipment commercially before required insurance is active"
        }
      ],
      "effects": [
        {
          "id": "E35",
          "type": "STATE_TRANSITION",
          "description": "Event of default declared",
          "new_state": "default"
        },
        {
          "id": "E35b",
          "type": "RULE_ACTIVATION",
          "description": "Activates default remedies",
          "target_rule_id": "R39"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R36",
      "type": "REPRESENTATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Event of default: unauthorized lien",
      "activation": "INACTIVE",
      "description": "Each of the following is an event of default: (c) Buyer grants or permits an unauthorized lien.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T36",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer grants or permits an unauthorized lien on Equipment"
        }
      ],
      "effects": [
        {
          "id": "E36",
          "type": "STATE_TRANSITION",
          "description": "Event of default declared",
          "new_state": "default"
        },
        {
          "id": "E36b",
          "type": "RULE_ACTIVATION",
          "description": "Activates default remedies",
          "target_rule_id": "R39"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R37",
      "type": "REPRESENTATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Event of default: material misrepresentation",
      "activation": "INACTIVE",
      "description": "Each of the following is an event of default: (d) Buyer materially misrepresents the Equipment's use, location, or insurance.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T37",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer materially misrepresents Equipment's use, location, or insurance"
        }
      ],
      "effects": [
        {
          "id": "E37",
          "type": "STATE_TRANSITION",
          "description": "Event of default declared",
          "new_state": "default"
        },
        {
          "id": "E37b",
          "type": "RULE_ACTIVATION",
          "description": "Activates default remedies",
          "target_rule_id": "R39"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R38",
      "type": "REPRESENTATION",
      "party": "Maria's Bakery LLC",
      "counterparty": "Neighborhood Bank, N.A.",
      "action": "Event of default: failure to maintain or protect Equipment",
      "activation": "INACTIVE",
      "description": "Each of the following is an event of default: (e) Buyer fails to maintain or protect the Equipment.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T38",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer fails to maintain or protect the Equipment"
        }
      ],
      "effects": [
        {
          "id": "E38",
          "type": "STATE_TRANSITION",
          "description": "Event of default declared",
          "new_state": "default"
        },
        {
          "id": "E38b",
          "type": "RULE_ACTIVATION",
          "description": "Activates default remedies",
          "target_rule_id": "R39"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R39",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Accelerate unpaid amounts upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T39",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E39",
          "type": "ACCELERATION",
          "description": "All unpaid amounts become immediately due and payable",
          "new_state": "accelerated"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R40",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Require immediate payment upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T40",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E40",
          "type": "PAYMENT",
          "description": "Lender demands immediate payment of all amounts due",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "Neighborhood Bank, N.A."
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R41",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Take possession of Equipment upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T41",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E41",
          "type": "ASSET_TRANSFER",
          "description": "Lender takes possession of Equipment as permitted by law",
          "new_state": "repossessed"
        }
      ],
      "constraints": [
        {
          "id": "C6",
          "type": "CONTROLLING_ITEM",
          "scope": [
            "R41"
          ],
          "description": "Repossession limited to what is permitted by applicable law"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R42",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Enforce security interest upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T42",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E42",
          "type": "FORFEITURE",
          "description": "Lender enforces security interest through foreclosure or other remedies",
          "new_state": "foreclosed"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R43",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Apply insurance proceeds upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T43",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs AND insurance proceeds available",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E43",
          "type": "PAYMENT",
          "description": "Lender applies insurance proceeds to outstanding obligations",
          "payment_to": "Neighborhood Bank, N.A."
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R44",
      "type": "POWER",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Recover reasonable enforcement costs upon default",
      "activation": "INACTIVE",
      "description": "Upon default, Lender may accelerate unpaid amounts, require immediate payment, take possession of the Equipment as permitted by law, enforce its security interest, apply insurance proceeds, and recover reasonable enforcement costs.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T44",
          "type": "EVENT_TRIGGER",
          "condition": "Event of default occurs",
          "threshold_field": "default_status",
          "threshold_value": "true",
          "threshold_operator": "eq"
        }
      ],
      "effects": [
        {
          "id": "E44",
          "type": "PAYMENT",
          "description": "Buyer owes Lender reasonable enforcement costs incurred",
          "payment_formula": "enforcement_costs",
          "payment_from": "Maria's Bakery LLC",
          "payment_to": "Neighborhood Bank, N.A."
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R45",
      "type": "POWER",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Suspend warranty service if Buyer fails to pay amounts owed to Dealer",
      "activation": "INACTIVE",
      "description": "Dealer may suspend any open warranty service to the extent permitted by law if Buyer has failed to pay amounts owed to Dealer.",
      "mappable": false,
      "unmappable_reason": "POWER is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T45",
          "type": "EVENT_TRIGGER",
          "condition": "Buyer fails to pay amounts owed to Dealer"
        }
      ],
      "effects": [
        {
          "id": "E45",
          "type": "STATE_TRANSITION",
          "description": "Dealer suspends open warranty service",
          "new_state": "warranty_suspended"
        }
      ],
      "constraints": [
        {
          "id": "C7",
          "type": "CONTROLLING_ITEM",
          "scope": [
            "R45"
          ],
          "description": "Suspension limited to extent permitted by applicable law"
        }
      ],
      "exceptions": []
    },
    {
      "id": "R46",
      "type": "COVENANT",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Assign manufacturer warranties to Buyer",
      "activation": "INACTIVE",
      "description": "Dealer assigns to Buyer available manufacturer warranties for the vehicle and refrigeration unit.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T46",
          "type": "EVENT_TRIGGER",
          "condition": "Delivery of Equipment to Buyer"
        }
      ],
      "effects": [
        {
          "id": "E46",
          "type": "ASSET_TRANSFER",
          "description": "Manufacturer warranties assigned from Dealer to Buyer"
        }
      ],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R47",
      "type": "REPRESENTATION",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "Maria's Bakery LLC",
      "action": "Dealer gives no warranty beyond express written warranties",
      "activation": "INACTIVE",
      "description": "Dealer gives no warranty beyond the express written warranties delivered with the Equipment.",
      "mappable": false,
      "unmappable_reason": "REPRESENTATION is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T47",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R48",
      "type": "COVENANT",
      "party": "Maria's Bakery LLC",
      "counterparty": "All",
      "action": "Agreement binds parties and permitted successors",
      "activation": "INACTIVE",
      "description": "This Agreement binds the parties and their permitted successors.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T48",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R49",
      "type": "COVENANT",
      "party": "ColdRoad Vans Inc.",
      "counterparty": "All",
      "action": "Agreement binds parties and permitted successors",
      "activation": "INACTIVE",
      "description": "This Agreement binds the parties and their permitted successors.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T49",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R50",
      "type": "COVENANT",
      "party": "Neighborhood Bank, N.A.",
      "counterparty": "All",
      "action": "Agreement binds parties and permitted successors",
      "activation": "INACTIVE",
      "description": "This Agreement binds the parties and their permitted successors.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T50",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R51",
      "type": "COVENANT",
      "party": "All",
      "counterparty": "All",
      "action": "Amendments must be in writing",
      "activation": "INACTIVE",
      "description": "Amendments must be in writing.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T51",
          "type": "EVENT_TRIGGER",
          "condition": "Any party seeks to amend Agreement"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R52",
      "type": "COVENANT",
      "party": "All",
      "counterparty": "All",
      "action": "Electronic signatures are effective",
      "activation": "INACTIVE",
      "description": "Electronic signatures are effective.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T52",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [],
      "exceptions": []
    },
    {
      "id": "R53",
      "type": "COVENANT",
      "party": "All",
      "counterparty": "All",
      "action": "California law governs except where federal law applies to Lender",
      "activation": "INACTIVE",
      "description": "California law governs except to the extent federal law applies to Lender.",
      "mappable": false,
      "unmappable_reason": "COVENANT is not in the four mappable primitives",
      "triggers": [
        {
          "id": "T53",
          "type": "DATE_TRIGGER",
          "condition": "Agreement effective date",
          "reference_date": "effective_date"
        }
      ],
      "effects": [],
      "constraints": [
        {
          "id": "C8",
          "type": "CARVE_OUT",
          "scope": [
            "R53"
          ],
          "description": "Federal law applies to Lender where applicable"
        }
      ],
      "exceptions": []
    }
  ]
}
```

---

- 2026-05-16: Ingested from DDKT Maria's Bakery output JSON for scenario optimization and deterministic FSM verification.
