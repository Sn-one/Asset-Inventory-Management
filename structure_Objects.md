# Shared
* Location
    - name
    - type
    - code
    - town/city
    - region
    - is_active

* user
    - igg
    - name
    - department

* Suplier / Vendor
    - id 
    - name 
    - address 
    - 

# Asset side

* Asset_category
    - name
    - code
    - description

* Asset
    - asset_id
    - name
    - description
    - category
    - location
    - serial_number
    - purchase_date
    - purchase_cost
    - condition
    - status
    - suplier_name
    - warrenty
    - notes/comments

* Asset_assignment
    - asset_id 
    - assignment_type 
    - from_location
    - to_location
    - assigned_to
    - moved_at
    - comments/notes

* maintenace_record
    - asset_id
    - date
    - maintenance_type 
    - description
    - cost
    - suplier_name


# Inventory side
* item_category
    - item_code
    - description

* item
    - item_code
    - name
    - description
    - item_category
    - uom

* stock
    - item_code
    - location
    - quantity

* stock_movement
    - item_code
    - movement_date
    - movement_type 
    - quantity
    - from_location
    - to_location
    - refrence
    - notes/comments
    