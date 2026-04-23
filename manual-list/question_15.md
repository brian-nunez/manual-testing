### Test #15: Motion and Gestures

1. Does the page use **dragging movement**[1](#footnote-motion-gestures-1) as input?
   
   - **YES**: Can the functionality that takes input from dragging movement also be operated using a **single pointer without dragging**?
     
     - **NO**: Is the functionality that takes input from dragging movement **essential**[2](#footnote-motion-gestures-2)? If not, raise an issue (2.5.7).
2. Does the page use **path-based gestures** or **multipoint gestures** as input?
   
   - **YES**: Can the functionality that takes input from path-based/multipoint gestures also be operated using a **single pointer without a path-based gesture**? If not, raise an issue (2.5.1, 2.5.1).
3. Does the page use **device motion** or **user motion** as input?
   
   - **YES**: Can the functionality that takes input from device/user motion also be operated by **user interface components** that do not require device/user motion? If not, raise an issue (2.5.4).
   - **YES**: Can motionbased operation be **disabled**? If not, raise an issue (2.5.4).

[\[1\]](#footnote-trigger-motion-gestures-1): A **dragging movement** is "an operation where the pointer engages with an element on the down-event and the element (or a representation of its position) follows the pointer until an up-event". [*WCAG 2.2*](https://www.w3.org/TR/WCAG22/#dfn-dragging-movements)

[\[2\]](#footnote-trigger-motion-gestures-2): A **essential** function is one that, "if removed, would fundamentally change the information or functionality of the content, and information and functionality cannot be achieved in another way that would conform". [*WCAG 2.2*](https://www.w3.org/TR/WCAG22/#dfn-essential)

