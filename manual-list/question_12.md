### Test #12: Tables

For each **data table** on the page, consider the following:

1. Does the **first row** of the table contain information that serves as a **caption** for the table rather than data?
   
   - **NO**: Proceed to the next question
   - **YES**: Raise an issue (1.3.1)
2. Can the table rows be **sorted** by specific column headers?
   
   - **NO**: Proceed to the next question
   - **YES**: Sort the table by one of the columns. Inspect the accessibility properties of the sorted header cell. Verify that *at least one* of the following statements are true. If not, raise an issue (4.1.2).
     
     - The cell's **accessible name** indicates that the table is sorted according to the information in current column
     - The cell has an **`aria-sort`** attribute whose value indicates the sorting direction ("ascending" or "descending")
3. Does the table's **root element** have a **`role="table"`** or **`role="grid"`** attribute?
   
   - **NO**: Stop testing this table and proceed to the next one
   - **YES**: Inspect the **markup** of the table, and consider each of the following:
     
     1. Is each **row**[1](#footnote-tables-1) *one* of the following? If not, raise an issue (1.3.1).
        
        - A **`<tr>`** element
        - An element with a **`role="row"`** attribute
     2. Is each **data cell** *one* of the following? If not, raise an issue (1.3.1).
        
        - A **`<td>`** element
        - An element with a **`role="cell"`** attribute
        - An element with a **`role="gridcell"`** attribute **and** the parent table has **`role="grid"`**
     3. Look at the data table's **header structure**[2](#footnote-tables-2). Select the **type** that best describes the table and follow the instructions:
        
        - **One Header**: *One simple column header or one simple row header, but not both.*
          
          - Is each **header cell** *one* of the following? If not, raise an issue (1.3.1).
            
            - A **`<th>`** element
            - An element with a **`role="columnheader"`** or **`role="rowheader"`** attribute
        - **Two Headers**: *One simple column header and one simple row header.*
          
          - Is each **header cell** *one* of the following? If not, raise an issue (1.3.1).
            
            - A **`<th>`** element with a **`scope="col"`** or **`scope="row"`** attribute
            - An element with a **`role="columnheader"`** or **`role="rowheader"`** attribute
        - **Irregular**: *Header cells span across multiple columns and/or rows.*
          
          - Look at each **header cell** and consider the following:
            
            - Select the **type** that best describes the header cell and follow the instructions:
              
              - **Header for a single column**
                
                - Are *all* of the following statements true? If not, raise an issue (1.3.1).
                  
                  - The header cell is a **`<th>`** element or else has a **`role="columnheader"`** attribute
                  - The header cell has a **`scope="col"`** attribute
                  - The header cell has a corresponding **`<col>`** element at the beginning of the table
              - **Header for a single row**
                
                - Are *both* of the following statements true? If not, raise an issue (1.3.1).
                  
                  - The header cell is a **`<th>`** element or else has a **`role="rowheader"`** attribute
                  - The header cell has a **`scope="row"`** attribute
              - **Header for a multiple columns**
                
                - Are *all* of the following statements true? If not, raise an issue (1.3.1).
                  
                  - The header cell is a **`<th>`** element or else has a **`role="columnheader"`** attribute
                  - The header cell has a **`scope="colgroup"`** attribute
                  - The header cell has a **`colspan="{n}"`** attribute where `n` equals the number of columns across which the header cell spans
                  - The header cell has a corresponding **`<colgroup>`** element at the beginning of the table with a **`span="{n}"`** attribute where `n` equals the number of columns across which the header cell spans
              - **Header for a multiple rows**
                
                - Are *all* of the following statements true? If not, raise an issue (1.3.1).
                  
                  - The header cell is a **`<th>`** element or else has a **`role="rowheader"`** attribute
                  - The header cell has a **`scope="rowgroup"`** attribute
                  - The header cell has a **`rowspan="{n}"`** attribute where `n` equals the number of rows across which the header cell spans
        - **Multi-level**: *Column headers repeat or change part-way through the table, or some data cells have three or more associated header cells.*
          
          - Look at each **header cell** and consider the following:
            
            - Is the header cell *one* of the following? If not, raise an issue (1.3.1, 1.3.1).
              
              - A **`<th>`** element
              - An element with a **`role="columnheader"`** or **`role="rowheader"`** attribute
            - Does the header cell have a (document-wide) **unique `id`** attribute? If not, raise an issue (1.3.1, 1.3.1).
          - Look at each **data cell** and consider the following:
            
            - Are *both* of the following statements true? If not, raise an issue (1.3.1, 1.3.1).
              
              - The data cell has either a **`headers`** or **`aria-labelledby`** attribute
              - The value of the **`headers`** or **`aria-labelledby`** attribute contains a space-delimited list of ids that correspond to *all* of the data cell's header cells

[\[1\]](#footnote-trigger-tables-1): `<thead>`, `<tbody>`, `<tfoot>`, and elements with `role="rowgroup"` may be used to group multiple rows together, but should not *themselves* be considered as rows.

[\[2\]](#footnote-trigger-tables-2): Refer to [Table Concepts](https://www.w3.org/WAI/tutorials/tables/) for more information about how to classify table headers.

