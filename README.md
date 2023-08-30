### Experiment Generator
Experiment generator allows for the automated creation, design, and storage of Chaos ToolKit experiments.

## CLI Tool

The CLI Tool simplifies access to the Generator API

It has 4 commands: package, app, scenario, generator

# Package 
Package handles parsing and extracting function signatures from action/probe modules. It has two subcommands, upload and delete and takes a file path to a zip file as an argument. 

Example - to upload run:
```
python generator_tool.py package upload "filepath" 
```

# App 
App handles target application configurations. It has two sub commands, init and onboarding. Init generates documentation for all stored scenarios stored in the Generator. Onboarding handles CRUD operations for target configurations and has 4 subcommands (create, get, update, delete) and takes a yaml file (path) as input. Refer to the samples for input structure.

Example - to upload run:
```
python generator_tool.py app onboarding create "yaml_filepath"
```

# Scenario 
Scenario handles CRUD operations for scenario configurations and operates similarly to app onboarding.

Example - to upload run:
```
python generator_tool.py scenario create "yaml_filepath"
```

# Generator 
Once scenarios and target app configs are loaded, generator handles experiment generation CRUD, though unlike scenario and app onboarding, it takes a string as input. The string should be formatted as "target app name-scenario name". There should be no '-' in target app name.

Example - to create run:
```
python generator_tool.py generator create "VR Trader-Kubernetes (EKS)-Worker Node-EC2-Resource-High Memory Utilization"
```