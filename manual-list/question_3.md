### Test #3: Page Structure

1. Inspect the page's **heading levels**.
   
   - Are the heading levels **out of order** in such a way that the structure of the page is not properly conveyed? If so, raise an issue (1.3.1).
   - Is one of the headings located at the **top** of the page's **main content area**?
     
     - **NO**: Does the page contain a **`<main>`** element or an element with a **`role="main"`** attribute?
       
       - **YES**: Does this element contain the page's **main content area**?
         
         - **NO**: Does the page contain a **skip link** as one of the first focusable elements that allows users to jump directly to the page's main content area?
           
           - **YES**: Activate the skip link. Does **browser focus move** to expected destination? If not, raise an issue (2.4.1).
           - **NO**: Raise an issue (2.4.1).
2. Does the page contain any **groups of navigation links**, or so-called "breadcrumb" components?
   
   - **YES**: Is each group of navigation links **identified** in *at least one* of the following ways? If not, raise an issue (1.3.1, 4.1.2, 4.1.2).
     
     1. The navigation links are together contained within a **`<nav>`** element.
     2. Each navigation link is contained within a **list item** (`<li>` or `role="listitem"`), and all the list items are together contained within a common **list** (`<ul>`, `<ol>`, or `role="list"`).
     3. Each navigation link is contained within a **menu item** (`role="menuitem"`), and all the menu items are together contained within a common **menu** (`role="menu"` or `role="menubar"`).
     4. The navigation links are preceded by a **heading** (`<h[1-6]>` or `role="heading"`) that identifies the group.
