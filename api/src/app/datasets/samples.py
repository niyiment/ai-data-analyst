"""Built-in sample datasets for one-click evaluation (US-06)."""

SAMPLE_DATASETS: dict[str, tuple[str, bytes]] = {
    "retail_sales": (
        "retail_sales.csv",
        (
            b"order_id,order_date,region,category,product,units,unit_price,revenue,returned\n"
            b"1001,2026-01-05,North,Electronics,Wireless Mouse,4,25.00,100.00,false\n"
            b"1002,2026-01-06,South,Furniture,Desk Chair,2,180.00,360.00,false\n"
            b"1003,2026-01-08,East,Electronics,USB-C Hub,5,40.00,200.00,true\n"
            b"1004,2026-01-10,West,Office Supplies,Notebook Pack,10,12.50,125.00,false\n"
            b"1005,2026-01-12,North,Furniture,Standing Desk,1,420.00,420.00,false\n"
            b"1006,2026-01-14,South,Electronics,Mechanical Keyboard,3,95.00,285.00,false\n"
            b"1007,2026-01-18,East,Office Supplies,Desk Lamp,4,35.00,140.00,false\n"
            b"1008,2026-01-20,West,Electronics,Monitor Stand,2,65.00,130.00,true\n"
        ),
    ),
}
