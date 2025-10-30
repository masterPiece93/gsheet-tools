# Gsheet Tools

- should be a pure python package
- long term vision : should serve almost all google sheet scenarios
    - classify a scenario , that can be aechieved from google sheets
    - all scenarios must be covered by package in following manner
        1. just expose support api's .
        2. provide in-built flows around various use cases of that scenario .
        3. complete job done kind of api's by parameterizing the dynamic factors  .
- must provide very good documentation rich with code snippets and sample demo's
- must provide Youtube Demo Videos .
- other aspects [ low priority ]
    - advertising & marketing


## Similar Libraries on PyPi

-   django-gsheets
-   public-google-sheets-backup
-   django-gsheets-import [v.I]
-   target-gsheet
-   gsheet-plotter [I]
-   gsheet-plots [I]
-   gsheet-manager [I]
-   gsheet-access [V.I]
-   mcp-google-sheets [V.V.I]
-   google-sheets-db [V.V.I] -> IDEA : using google sheets as ORM
-   google-sheets-helper -> IDEA : almost similar as mine
## Notes

while goin through all the packages above , there are 2 things that are very evident :
1. Project Description in PyPi page is very much useful in attaractng the developer to use it
2. `downloads:2k` kind of tag is very useful on PyPi Page
3. The Installation and usage guide on PyPi page should be very very concise and a Quickstarter
    - more and more links should be mentioned for detailed info
        - and that link should containe more and more code snippets .
4. When developing a wrapper/tool for a google product , we must have to support all the types of auth mechanisms supported by google .
5. If we are targeting pandas dataframe , then we'll have to support all the functions supported by pandas .

#### Ideas

- you have done EDA before , so it will be very very useful if you'll provide EDA on google sheets data
    - if you are supporting charting , then you'll have to support all types of charts .
