# Survivorship rules

| Attribute | Strategy |
|---|---|
| npi | Source priority hcp_master > crm > specialty > rx_demand; must pass checksum |
| names | Source priority then non-null |
| practice_address | Most recent non-null |
| do_not_contact | Most restrictive always wins |
| sample_eligible | not do_not_contact |
