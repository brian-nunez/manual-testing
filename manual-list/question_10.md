### Test #10: Status Messages

- Does the page produce any **status messages**[1](#footnote-status-messages-1)?
  
  - **YES**: For each unique status message, perform the following steps:
    
    1. Activate a screen reader.
    2. Produce the status message.
    3. Is the status message **announced immediately** by the screen reader? If not, raise an issue (4.1.3).
    4. Does the status message **disappear by itself**, without being actively dismissed by the user?
       
       - **YES**: Does the status message **disappear** while the **status it describes is still applicable**? For example, if the message indicates that there was a problem with a submitted form, does the message disappear while the error still exists?
         
         - **YES**: Is the **same information** conveyed by the status message also available on the page **in some other way**? If not, raise an issue (2.2.1).

[\[1\]](#footnote-trigger-status-messages-1): A **status message** is a "change in content that is not a [change of context](https://www.w3.org/TR/WCAG21/#dfn-change-of-context), and that provides information to the user on the success or results of an action, on the waiting state of an application, on the progress of a process, or on the existence of errors." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-status-messages).

