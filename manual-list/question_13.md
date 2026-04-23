### Test #13: Time Limits

- Does the page impose any **time limits** on the user?
  
  - **YES**: Is *at least one* of the following statements true?
    
    - The time limit is longer than **20 hours**.
    - The user can **turn off** the time limit before encountering it.
    - The user can **adjust** the time limit to at least **ten times** its default duration before encountering it.
    - The time limit is a required part of a **real-time event** (for example, an auction), and no alternative to the time limit is possible.
    - The time limit is **essential**[1](#footnote-time-limits-1) and extending it would invalidate the activity.
      
      - **YES**: You may **stop this test**.
      - **NO**: Turn on a screen reader and wait for the time limit to expire. Does the page **warn** the user before the time limit expires?
        
        - **NO**: Raise an issue (2.2.1).
        - **YES**: Is the warning **announced immediately** by the screen reader?
          
          - **NO**: Raise an issue (2.2.1).
          - **YES**: Does the user have at least **20 seconds** to extend the time limit with a simple action (for example, "Press the Space Bar to extend your session")?
            
            - **NO**: Raise an issue (2.2.1).
            - **YES**: Can the user access and activate the extension mechanism using only the **keyboard and screenreader**?
              
              - **NO**: Raise an issue (2.2.1).
              - **YES**: Can the user extend the time limit in this way at **least ten times**?
                
                - **NO**: Raise an issue (2.2.1).

[\[1\]](#footnote-trigger-time-limits-1): **essential** meaning "if removed, would fundamentally change the information or functionality of the content, **and** information and functionality cannot be achieved in another way that would conform." [*WCAG 2.1 Glossary*](https://www.w3.org/TR/WCAG21/#dfn-essential).

