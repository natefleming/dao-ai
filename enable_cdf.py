# Databricks notebook source
# COMMAND ----------

# Enable Change Data Feed on dim_stores2 table
# This is required for Delta Sync vector search indexes

# COMMAND ----------

# Enable Change Data Feed on dim_stores2
spark.sql("""
    ALTER TABLE demos_genie.rcg_store_manager_gold.dim_stores2 
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")

print("Change Data Feed enabled on dim_stores2 table")

# COMMAND ----------

# Verify the table properties
table_details = spark.sql("""
    DESCRIBE DETAIL demos_genie.rcg_store_manager_gold.dim_stores2
""").collect()

print("Table details:")
for row in table_details:
    print(f"Table Properties: {row.properties}")

# COMMAND ----------

# Check if Change Data Feed is enabled
properties = spark.sql("""
    SHOW TBLPROPERTIES demos_genie.rcg_store_manager_gold.dim_stores2
""").collect()

print("\nTable Properties:")
for prop in properties:
    print(f"{prop.key}: {prop.value}")
    if prop.key == "delta.enableChangeDataFeed":
        if prop.value == "true":
            print("✅ Change Data Feed is ENABLED")
        else:
            print("❌ Change Data Feed is NOT enabled")

# COMMAND ----------

# Also enable CDF on products table if it's not already enabled
try:
    spark.sql("""
        ALTER TABLE demos_genie.rcg_store_manager_gold.products 
        SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
    """)
    print("Change Data Feed enabled on products table")
except Exception as e:
    print(f"Products table CDF status: {str(e)}")

# COMMAND ---------- 