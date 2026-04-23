### Test #7: Forms

1. Does the page contain any form fields that **collect information about the user**?
   
   - **YES**: For each form field, consider the following:
     
     - Is the **purpose** of the form field included in the [Input Purposes for User Interface Components](https://www.w3.org/TR/WCAG21/#input-purposes) list?
       
       - **YES**: Are *both* of the following statements true? If not, raise an issue (1.3.5).
         
         - The form field has an **`autocomplete`** attribute.
         - The **value** of the `autocomplete` attribute **matches the purpose** of the input (according to the [Input Purposes for User Interface Components](https://www.w3.org/TR/WCAG21/#input-purposes) list).

