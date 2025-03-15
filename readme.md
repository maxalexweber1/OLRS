# Over-Leveraged Risk Score (OLRS) for Cardano Native Tokens

## 1. Purpose
The Over-Leveraged Risk Score (OLRS) is a quantitative metric designed to assess the risk of over-leveraging in lending positions involving Cardano Native Tokens (e.g., SNEK, IAG, BTN, LENFI). It evaluates a token’s systemic risk in lending scenarios by analyzing the average health of all lending positions for that token alongside its market characteristics.

**Score Interpretation:**
- **0-50:** Low risk (safe lending positions).
- **50-75:** Moderate risk (caution advised).
- **75-100:** High risk (nearing liquidation threshold).

OLRS focuses on **pre-liquidation scenarios** (Avg HS ≥ 1), as positions with Avg HS < 1 are typically already liquidated / going to get defaulted.

## 2. Background and Motivation
In DeFi lending on Cardano (e.g., Lenfi, Levvy), tokens serve as collateral to borrow ADA. Over-leveraging occurs when the collateral value approaches or falls below the loan value, increasing liquidation risk. While traditional metrics like Loan-to-Value (LTV) focus on individual positions, OLRS evaluates:
- **Systemic lending risk** via the **average Health Score (Avg HS)**.
- **Token-specific risk factors**, including **volatility, liquidity, and market capitalization**.
- **Consistency with DeFi risk management principles** (e.g., MakerDAO’s collateralization ratios).

## 3. Methodology
The OLRS integrates four key risk factors, each weighted to reflect its contribution to over-leverage risk:

| **Factor** | **Definition** | **Weight** |
|-----------|--------------|------------|
| **Avg HS** | Measures mean collateral-to-loan ratio across all lending positions | **0.55** |
| **Volatility (V)** | Measures price fluctuation risk | **0.15** |
| **Liquidity (L)** | Assesses token's tradability and execution risk | **0.2** |
| **Market Capitalization (MC) in ADA** | Determines token’s size and manipulation resistance | **0.1** |

## 4. Formula

The **OLRS** formula is composed of four weighted components, each representing a different risk factor.

### **Formula:**
$$
\text{OLRS} = 0.55 \times \min\left(100 \times (4 - \text{Avg HS}), 100\right) +
0.15 \times \left(\frac{V + V^2}{2} \times 100\right) +
0.2 \times \left(\left(1 - \min\left(\frac{L}{250{,}000}, 1\right)\right)^2 \times 100\right) +
0.1 \times \left(\frac{10 - \log_{10}(\max(MC_{\text{ADA}}, 10^6))}{4} \times 100\right)
$$

### **Explanation of Terms:**

1. **Health Score Impact (55%)**
   - Formula:  
     $$ 0.55 \times \min(100 \times (4 - \text{Avg HS}), 100) $$
   - **Factor:** *Avg HS* (Average Health Score)
   - **Effect:** Higher health scores lead to a lower OLRS value.
   - **Explanation:**
     - \( 4 - Avg HS ) ensures that higher scores reduce the contribution.
     - The multiplication by 100 scales the result.
     - The **minimum function** ensures the term does not exceed 100.
     - **Weight:** 55% (largest influence).

2. **Volatility Impact (15%)**
   - Formula:  
     $$ 0.15 \times \left(\frac{V + V^2}{2} \times 100\right) $$
   - **Factor:** *V* (Volatility)
   - **Effect:** Higher volatility increases the OLRS value.
   - **Explanation:**
     - ( V + V^2 ) accounts for both linear and exponential volatility effects.
     - Division by 2 smooths the influence.
     - The multiplication by 100 scales the result.

3. **Liquidity Impact (20%)**
   - Formula:  
     $$ 0.2 \times \left(\left(1 - \min\left(\frac{L}{250{,}000}, 1\right)\right)^2 \times 100\right) $$
   - **Factor:** *L* (Liquidity)
   - **Effect:** Higher liquidity lowers the OLRS value.
   - **Explanation:**
     - \( L / 250000 \) normalizes liquidity to a range of 0 to 1.
     - **Min function** ensures values don’t exceed 1.
     - \( 1 - \) ensures that higher liquidity results in a lower OLRS.
     - The **squared term** penalizes lower liquidity more heavily.
     - The multiplication by 100 scales the result.

4. **Market Capitalization Impact (10%)**
   - Formula:  
     $$ 0.1 \times \left(\frac{10 - \log_{10}(\max(MC_{\text{ADA}}, 10^6))}{4} \times 100\right) $$
   - **Factor:** *MC_ADA* (Market Capitalization in ADA)
   - **Effect:** Higher market capitalization lowers the OLRS value.
   - **Explanation:**
     - The **max function** ensures a minimum market cap of \(10^6\), preventing negative logarithms.
     - \( \log_{10} \) computes the logarithm of the market cap.
     - \( 10 - \log_{10}(MC_{ADA}) \) penalizes smaller projects more.
     - Division by 4 smooths the impact.
     - The multiplication by 100 scales the result.

---

## **Summary of Influences:**
- **Health Score (55%)** – Higher value = lower OLRS.
- **Volatility (15%)** – Higher value = higher OLRS.
- **Liquidity (20%)** – Higher value = lower OLRS.
- **Market Cap (10%)** – Higher value = lower OLRS.

---

### **Scaling Adjustments:**
- **Avg HS Component:**
  - **HS < 1 → 100** (Liquidation threshold)
  - **HS ≥ 3 → 0** (Safe zone)
  - **1 ≤ HS < 3 → Scaled linearly from 100 to 0**
- **Liquidity Adjustment:**
  - Liquidity risk is amplified for volumes **below 1M ADA**.
- **Market Cap Floor:**
  - Ensures MC component doesn’t create extreme outliers for micro-cap tokens.
- **Market Cap in ADA:**
  - Market Cap (MC) is always calculated in **ADA**, not USD.

## 5. Data Sources & Input Requirements
### **Inputs:**
| **Parameter** | **Definition**
|--------------|--------------|
| **Avg HS** | Avg health score across all open lending positions| 
| **V** | Annualized price volatility (normalized 0-1) |
| **L** | 24-hour trading volume (ADA)
| **MC** | Total market capitalization in ADA

### **Processing Steps:**
1. Gather input data for a given token.
2. Apply values to the OLRS formula.
3. Interpret the result:
   - **<50** → Safe for lending.
   - **50-75** → Monitor closely.
   - **>75** → High risk, potential over-leverage.

## 6. Limitations & Considerations
### **Potential Limitations:**
- **Data Dependency:** Accuracy of OLRS depends on **reliable Avg HS data** from lending platforms.
- **Static Weights:** Fixed weights may not fully adapt to extreme market conditions but ensure consistency.
- **Assumptions in Liquidity Calculation:** Scaling is adjusted for **volumes <250k ADA**, but may require further refinement.
- **Market Cap in ADA:** Since prices fluctuate, some variations in the ADA-equivalent MC may occur. Just calculated with Ciculating supply from taptools * price so maybe need to better adjust this

