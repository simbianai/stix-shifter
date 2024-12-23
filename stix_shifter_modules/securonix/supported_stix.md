# Securonix

## Supported STIX Mappings

### Results STIX Domain Objects

*   Identity
*   Observed Data

### Supported STIX Operators

| STIX Operator | Data Source Operator |
|--|--|
| AND (Comparison) | AND |
| OR (Comparison) | OR |
| = | = |
| != | != |
| > | > |
| >= | >= |
| < | < |
| <= | <= |
| IN | IN |

### Searchable STIX objects and properties

| STIX Object and Property | Mapped Data Source Fields |
|---|---|
| **x-oca-event**:action | action |
| **x-oca-event**:description | description |
| **x-oca-event**:category | category |
| **x-oca-event**:severity | severity |
| **x-oca-event**:created | eventtime |
| **x-oca-event**:user_ref.account_login | username |
| **ipv4-addr**:value | sourceip, destinationip |

### Supported STIX Objects and Properties for Query Results
| STIX Object | STIX Property | Data Source Field |
|--|--|--|
| x-oca-event | action | action |
| x-oca-event | description | description |
| x-oca-event | category | category |
| x-oca-event | severity | severity |
| x-oca-event | created | eventtime |
| x-oca-event | user_ref | username |
| ipv4-addr | value | sourceip |
| ipv4-addr | value | destinationip |