
# Developer Notes


1. add pdm in pipx
```sh
pipx install --suffix "@gsheet-tools" pdm --python python3.12
```

2. prepare pdm
- as we already have `pdm.lock` file
```sh
pdm@gsheet-tools sync
```


## Bulding this package with pdm

- [Video Tute 1](https://www.youtube.com/watch?v=qOIWNSTYfcc)
    
    KeyPoints
    -   explained briefly - why we need **pipx**
    -   initializing a new project with pdm
    -   concept of groups in pdm
    -   customizing .vscode settings.json for pdm

    > little outdated .

    > recommended watch speed : 1.25x

.

- [Video Tute 2](https://www.youtube.com/watch?v=cOFyf0_CDhI)
    
    KeyPoints
    -   explained why to choose *pdm* over *poetry*
    -   explained in detail - why we need **pipx**
    -   initializing a new project with pdm
    -   dependency installation not explained in much detail
    
    > latest and fresh .

    > recommended watch speed : 1.25x

.

- [Video Tute 3](https://www.youtube.com/watch?v=wh8RUrg6f6o&t=399s)

    KeyPoints
    - 
    -   concept of groups in pdm
    -   dependency installation explained in detail
    -   doesn't use pipx , nor explains about it .

## Nox

#### Install Nox

```sh
pipx install --suffix "@gsheet-tools" nox --python python3.12
```
- If Alias Required :
    - pipx install <package_name> --alias <desired_alias> --python python3.12

#### Run Nox

Run
```sh
nox@gsheet-tools -s test_python_versions
```

Run and update nox-output.log
```sh
nox@gsheet-tools -s test_python_versions &> output.log
```