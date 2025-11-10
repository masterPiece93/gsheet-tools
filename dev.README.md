

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