---
type: contract-fsm-brief
title: "Maria's Bakery - Cross-Contract Decision Brief"
tags: [marias-bakery, contract-fsm, decision-brief, executable-contract]
---

# Maria's Bakery - Cross-Contract Decision Brief

This page connects the four ingested FSMs for business questions about route revenue, van readiness, landlord consent, insurance timing, supplier minimums, supplier rebates, late delivery credits, and termination risk.

The reasoner generates candidate scenarios, scores them against the user's desired outputs, then replays the event list through each FSM before presenting a recommendation.

## Source Context

```text
MARIA'S BAKERY CONTEXT, QUESTION, AND EXPECTED RESPONSE

1. THE BUSINESS CONTEXT

Maria's Bakery is a small neighborhood bakery in Mill Valley. It currently
makes most of its money from walk-in retail sales, but it has a chance to add
a wholesale breakfast route for Three Oaks Cafe Group.

The new route would pay Maria's Bakery $18,000 per month if Maria can deliver
fresh breakfast products to the customer locations by 7:00 a.m. every weekday.
This is attractive because it could stabilize cash flow, help the bakery use
more of its kitchen capacity, and justify buying a refrigerated delivery van.

The problem is timing. Maria wants to buy a refrigerated van near year-end,
but the van is only useful if several other things happen in time:

- The van must be delivered.
- Commercial auto insurance and refrigerated cargo/spoilage coverage must be
  active before the van is used for deliveries.
- The landlord must allow refrigerated vehicle parking/loading at the bakery.
- The supplier relationship must support the extra ingredient volume.
- The wholesale customer must receive timely deliveries.

Contrived business facts for the question:

- Maria's Bakery has $32,000 of usable cash.
- Normal monthly storefront rent is $6,200.
- The refrigerated van costs $58,000.
- Maria must pay $8,000 down at signing.
- The bank loan payment is $1,175 per month after delivery.
- The insurance broker says the commercial insurance binder might be active
  within 4 days, but it could slip to 18 days if underwriting asks for more
  documents.
- The wholesale route would produce $18,000 of monthly revenue.
- Each late delivery creates a $250 customer credit.
- Three late or missed deliveries in a month lets the customer put the
  account at-risk or terminate.
- The supplier monthly minimum is $4,500 once the wholesale route is signed.
- If Maria buys at least $8,000 of ingredients in a month, she earns a $400
  supplier rebate.
- For tax modeling only, Maria cares whether the van is actually available
  for regular bakery delivery use before year-end. The contracts do not decide
  tax treatment, but they do record operational facts that matter to that
  analysis.

2. THE QUESTION TO ASK

Ask:

"Should Maria's Bakery sign the wholesale route and buy the refrigerated van
now, or should she wait or use a rental bridge first? Explain the decision
using the four contracts, the money facts, the insurance risk, and the timing
of the delivery obligations."

3. HOW THIS SHOWS UP IN THE CONTRACTS

In contracts/C_VAN_contract.txt:

- Section 1.2 says the van price is $58,000 and the down payment is $8,000.
- Section 4 says Maria cannot use the van for commercial delivery until the
  required insurance is active.
- Section 4.3 says that if the van is delivered before the binder is active,
  it sits in a delivered-but-uninsured status and cannot be used for customer
  deliveries.
- Section 5.1 says the van can be treated as placed in business delivery
  service only after delivery, insurance, availability for regular bakery
  delivery, and more-than-50% business use are all true.
- Section 6.1 says the monthly bank payment is $1,175.

In contracts/C_LEASE_contract.txt:

- Section 2.1 says rent is $6,200 per month.
- Section 3.2 limits loading to 6:00 a.m. through 8:00 a.m. unless the
  landlord approves another window.
- Section 4 says Maria needs landlord consent before parking or operating a
  refrigerated vehicle at the premises overnight.
- Section 5 says unauthorized loading or refrigerated vehicle activity creates
  a $350 fee and must be cured within ten days.

In contracts/C_SUPPLIER_contract.txt:

- Section 2 says the supplier minimum is dormant until Maria signs a wholesale
  breakfast delivery contract.
- Section 3.1 says the monthly minimum is $4,500 once active.
- Section 5.1 says Maria earns a $400 rebate if monthly product purchases
  reach $8,000.
- Section 6 says supplier cold-chain failures can interfere with the breakfast
  route and require cooperation.

In contracts/C_WHOLESALE_contract.txt:

- Section 1.2 sets the route start date as January 1, 2027.
- Section 3.1 requires weekday delivery by 7:00 a.m.
- Section 3.4 says vehicle unavailability, supplier issues, staffing problems,
  traffic, or insurance delays do not automatically excuse late delivery.
- Section 4.1 says the monthly route price is $18,000.
- Section 5.1 says each late delivery creates a $250 credit.
- Section 6 says three late or missed deliveries can put the account at-risk
  and may allow termination.

4. EXPECTED RESPONSE

The expected answer should not simply say "buy the van" or "do not buy the
van." It should say the decision depends on whether Maria can make the van
legally and operationally usable before the wholesale route starts.

Expected response in simple English:

"Maria should only buy the van and sign the wholesale route immediately if
she can get the insurance binder active, get landlord consent, and have the
van ready for regular bakery delivery before the first required customer
deliveries. If those conditions are met, the van supports the $18,000 monthly
route, helps Maria reach the $8,000 supplier rebate threshold, and creates
the operational facts needed for later tax analysis.

If the insurance binder slips, buying the van becomes risky. The van can be
delivered but still unusable for commercial deliveries. The wholesale contract
does not excuse late deliveries just because insurance is delayed. Maria could
owe $250 per late delivery, lose the customer after three misses, still owe
supplier minimum purchases, and still owe the bank payment.

The safer business answer is either:

1. Buy now only after confirming insurance and landlord consent will be ready
   before deliveries begin; or
2. Use a short-term refrigerated rental bridge for the first route period,
   then buy the van after the insurance and service timing is certain.

The rental bridge may cost extra, but it protects the $18,000 customer route
from being lost because the owned van is delivered but not insured."

5. WHAT A GOOD SYSTEM SHOULD NOTICE

A good contract reasoning system should connect the four documents:

- The van contract creates the key timing problem: delivered is not the same
  as insured, and insured is not the same as placed in service.
- The wholesale contract turns that timing problem into real money risk:
  $250 credits and possible termination after three misses.
- The supplier contract adds a second money risk: the $4,500 minimum activates
  once the wholesale route is signed, even if deliveries become difficult.
- The lease can block the plan if refrigerated vehicle consent is missing or
  loading rules are violated.
- The tax question should be treated carefully. The contracts provide facts
  about use, insurance, and service date, but they do not themselves decide
  the tax result.
```

---

- 2026-05-16: Created as the cross-contract retrieval page for Maria's Bakery FSM optimization.
