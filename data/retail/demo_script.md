# BrickMart Companion App Demo Script
## Scenario: AI-Powered Store Associate Assistant

**Setting**: Store associate Sarah is working the footwear section at BrickMart's Downtown Market location. She's equipped with the BrickMart Companion app on her mobile device, powered by AI agents on the Databricks Lakehouse Platform.

**Characters**: 
- Sarah (Store Associate)
- Customer looking for sneakers
- BrickMart Companion AI Assistant

---

### **Scene 1: Customer Approach & Initial Query**

**Customer**: *approaches Sarah in the footwear section* "Excuse me, do you have the Adidas Gazelle sneakers in black? I've been looking everywhere for them."

**Sarah**: "Absolutely! Let me check our inventory for you right away." 
*[Opens BrickMart Companion app and speaks to AI assistant]*
"Hey Assistant, can you check if we have Adidas Gazelle sneakers in black at our Downtown Market location?"

**AI Assistant** *(through app)*: "Checking inventory now, Sarah... I see that Downtown Market is currently out of stock of Adidas Gazelle sneakers in black. However, I have some good news - we do have Gazelles in other colors here: navy (15 pairs) and grey (9 pairs, low stock). Both are in Aisle 5A. The next shipment with black Gazelles is scheduled for March 18th."

**Sarah**: *to customer* "I'm sorry, we're currently out of the black Gazelles, but I have a few options for you. We do have the same shoe in navy and grey right here in our store, or I can help you find them at nearby locations."

---

### **Scene 2: AI-Powered Recommendations**

**Customer**: "Hmm, I really wanted black. What else do you have that's similar?"

**Sarah**: *to app* "Assistant, can you recommend similar sneakers to the black Gazelles that we have in stock?"

**AI Assistant**: "Based on the customer's interest in Adidas Gazelle sneakers in black, here are my top recommendations from your current inventory:

- **Adidas Gazelle - Navy**: $89.99, 15 pairs available, Aisle 5A - Same classic style, just different color
- **Adidas Samba Classic - Black/White**: $94.99, 20 pairs available, Aisle 5A - Similar retro vibe with the iconic gum sole
- **Adidas Superstar - Black/White**: $99.99, 22 pairs available, Aisle 5A - Classic shell toe design in black colorway

All of these have similar styling and are very popular alternatives."

**Sarah**: *to customer* "So I have some great alternatives for you. The Samba in black and white has that same retro feel as the Gazelle, and the Superstar is a classic that never goes out of style. Would you like to see any of these? They're all right here in Aisle 5A."

---

### **Scene 3: Cross-Store Inventory Check**

**Customer**: "Those are nice, but I really have my heart set on the black Gazelles specifically. Are there other BrickMart stores nearby that might have them?"

**Sarah**: *to app* "Assistant, can you check which nearby stores have black Gazelles in stock?"

**AI Assistant**: "Absolutely! I found black Adidas Gazelles at these nearby BrickMart locations:

- **Marina Market** - 2200 Chestnut Street
  - 12 pairs in stock, Aisle 3A
  - 2.1 miles from here, about 8 minutes by car
  - Open until 10:00 PM tonight

- **Mission Market** - 2128 Mission Street  
  - 18 pairs in stock, Aisle 6C
  - 2.8 miles from here, about 12 minutes by car
  - Open until 11:00 PM tonight

Both locations have good availability!"

**Sarah**: *to customer* "Great news! I found them at two nearby stores. The Marina location is closest - just 8 minutes away and they have 12 pairs. The Mission store has even more stock with 18 pairs. Both are open late tonight. Which one works better for you?"

---

### **Scene 4: Personalized Service & Hold Request**

**Customer**: "The Marina store is perfect - it's right on my way home! Could you call them and have them hold a pair in size 10 for me?"

**Sarah**: *to app* "Assistant, can you place a hold on black Gazelles, size 10, at Marina Market for this customer?"

**AI Assistant**: "I'm processing that request now... Done! I've placed a 24-hour hold on 1 pair of Adidas Gazelle sneakers in black, size 10, at Marina Market. The hold is under the name you'll provide. 

I can also:
- Send store directions directly to the customer's phone
- Add this item to their shopping preferences for future notifications
- Set up an alert when Downtown Market restocks black Gazelles

What would be most helpful?"

**Sarah**: *to customer* "Perfect! I've got a pair held for you at Marina Market for 24 hours. I can text you the directions, and if you'd like, I can also set you up to get notified when we get black Gazelles back in stock here at Downtown. What's your phone number?"

**Customer**: "That's amazing service! Yes, please send me the directions and sign me up for the restock notifications."

**Sarah**: *to app* "Assistant, please send directions to Marina Market and set up restock notifications for black Gazelles."

**AI Assistant**: "Directions sent! Restock notifications are now active. The customer will receive a text when black Gazelles arrive at Downtown Market."

---

### **Demo Conclusion for Presenter**

**Sarah**: *to customer* "You're all set! Your black Gazelles are waiting at Marina Market, and you'll hear from us as soon as we get them back in stock here. Is there anything else I can help you find today?"

---

**Presenter Notes**: This demonstration showcases how the BrickMart Companion app transforms the associate experience:

- **Real-time inventory access** across all locations via Delta Live Tables
- **AI-powered recommendations** using Vector Search and MLflow models  
- **Seamless cross-store coordination** through Unity Catalog data governance
- **Personalized customer service** with automated holds and notifications
- **Natural conversation flow** between associate, AI assistant, and customer

The AI assistant handles complex inventory queries, recommendations, and service requests, allowing Sarah to focus on building customer relationships and providing exceptional service. This is the future of retail - where technology amplifies human expertise rather than replacing it.
