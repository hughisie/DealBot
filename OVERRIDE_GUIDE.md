# 📋 DealBot Manual Override Guide

## 🎯 What's New

You now have **full manual control** over which deals to publish!

---

## 📊 Understanding the Preview Table

### **Columns Explained:**

| Column | What It Shows |
|--------|---------------|
| **Select** | **✅ Publish** or **❌ Skip** - Shows what will happen when you publish |
| **Title** | Product name |
| **ASIN** | Amazon product ID |
| **Price** | Current validated price from Amazon |
| **PVP** | Original list price (Precio de Venta al Público) |
| **Discount** | Discount percentage (e.g., "-31%") |
| **Rating** | ⭐ Customer rating + review count from Amazon PA-API |
| **Stock** | Real-time availability status |
| **Status** | Overall deal status |

---

## 🏷️ Status Meanings

### ✅ **Ready**
- Product is in stock
- Price validated
- No issues detected
- **Will be published**

### ⚠️ **Price Check**
- Price difference > 15% between TXT file and Amazon
- **Example**: TXT says €0.01 but Amazon shows €10.99
- **Not an error** - just means you should verify the price is correct
- Deal **can still be published** (you decide!)

### ❌ **Out of Stock**
- Product unavailable on Amazon
- No current price available
- **Will be skipped automatically**
- You can still override to publish anyway (not recommended)

---

## 🔄 How to Override Publishing Decisions

### **Automatic Behavior** (Default)
When you load a file:
- ✅ In-stock deals → Marked "✅ Publish"
- ❌ Out-of-stock deals → Marked "❌ Skip"

### **Manual Override Steps**

1. **Select row(s)** in the table
   - Click on a deal to select it
   - Hold Cmd/Ctrl for multiple selections

2. **Click "Toggle Selected (Override)"**
   - Changes **✅ Publish** → **❌ Skip**
   - Changes **❌ Skip** → **✅ Publish**

3. **Review the changes**
   - Table updates immediately
   - Status log shows what changed

4. **Click "Publish Marked Deals"**
   - Only deals marked "✅ Publish" will be published
   - Deals marked "❌ Skip" are ignored

---

## 📝 Example Workflow

### Scenario 1: Skip a Deal with Price Issues

```
Deal 1: Status "⚠️ Price Check" - auto set to "✅ Publish"
↓
You want to review it first
↓
1. Select the row
2. Click "Toggle Selected (Override)"
3. Now shows "❌ Skip"
4. It won't be published
```

### Scenario 2: Force Publish an Out-of-Stock Deal

```
Deal 2: Status "❌ Out of Stock" - auto set to "❌ Skip"
↓
You know it will be back in stock soon
↓
1. Select the row
2. Click "Toggle Selected (Override)"  
3. Now shows "✅ Publish"
4. It will be published (not recommended!)
```

### Scenario 3: Publish Only Selected Deals

```
3 deals loaded:
Deal 1: ✅ Publish (in stock)
Deal 2: ✅ Publish (in stock)
Deal 3: ✅ Publish (in stock)
↓
You only want to publish Deal 1 and 3
↓
1. Select Deal 2
2. Click "Toggle Selected (Override)"
3. Deal 2 now shows "❌ Skip"
4. Click "Publish Marked Deals"
5. Only Deal 1 and 3 are published
```

---

## 🚀 Quick Start

1. **Select TXT File** → App processes all deals
2. **Review the preview table** → See prices, stock, ratings
3. **Override any decisions** → Select rows + Toggle
4. **Publish Marked Deals** → Only "✅ Publish" deals go live

---

## 💡 Tips

✅ **Best Practice**: Only override when you have a good reason
⚠️ **Price Check Deals**: Review the price difference before publishing
❌ **Out of Stock**: Don't publish unless you're certain it's a temporary issue
📊 **Use the preview**: All info is visible before publishing - no surprises!

---

## 🎊 Summary

| Feature | Benefit |
|---------|---------|
| **Automatic decisions** | Smart defaults - in-stock = publish, out-of-stock = skip |
| **Manual override** | You have the final say on every deal |
| **Clear indicators** | ✅ Publish / ❌ Skip - always know what will happen |
| **Full preview** | See prices, discounts, ratings, stock before publishing |
| **Status warnings** | ⚠️ alerts you to potential issues |

**You're in full control! 🎮**
