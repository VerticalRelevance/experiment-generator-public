import yaml
import json
import map_final
import map_middle

class ChaosExperiment:
    def __init__(self):
        self.title = ""
        self.description = ""
        self.config = {}
        self.steady_state_hypothesis = {}
        self.method = []
        self.rollbacks = []
        self.store_name = ""

    def set_steady_state_hypothesis(self, title, probes):
        self.steady_state_hypothesis['title'] = title
        self.steady_state_hypothesis['probes'] = probes

    def add_congig(self, items):
        for k, v in items.items():
            self.config[k] = {
                "type": "env",
                "key": v
            }
                
    def save_sig(self, data):
        self.store_name = f"{data['name']}_{data['type']}"
        filename = f"signatures/{self.store_name}_config.json"
        with open(filename, 'w') as file:
            json.dump(data, file)

    def create(self, input):
        
        # Store signature and initialize title and description
        self.save_sig(input)
        self.title = f"{input['type']} {input['service']} for {input['name']}"
        self.description = f"Can {input['name']} survive a {input['type']} {input['service']} experiment?"

        # Create steady state hypothesis
        steady_state_key = f"{input['service']} steady state"
        steady_state_mm = map_middle.probe_mid_maps[steady_state_key]
        steady_state_probes = []
        steady_state_probes = [map_final.map_probes[i] for i in steady_state_mm]
        self.set_steady_state_hypothesis(steady_state_key, steady_state_probes)
        
        # Create method
        method_key = f"{input['service']} {input['type']}"

        method_actions_sequence = map_middle.actions_mid_maps[method_key]
        fin_actions = [map_final.map_actions[i] for i in method_actions_sequence]

        method_probes_sequence = map_middle.probe_mid_maps[method_key]
        fin_probes = [map_final.map_probes[i] for i in method_probes_sequence]

        self.method += fin_actions+fin_probes

        # Populate configurations
        # If no configs, should we have mappings for a default configuration?
        self.add_congig(input['config'])

    def generate_yaml(self):
        experiment_data = {
            'title': self.title,
            'description': self.description,
            'configuration': self.config,
            'steady-state-hypothesis': self.steady_state_hypothesis,
            'method': self.method,
            'rollbacks': self.rollbacks,
        }
        
        yaml_data = yaml.dump(experiment_data, sort_keys=False)
        
        # Save the YAML to a file in the experiments directory
        filename = f'experiments/{self.store_name}.yaml'
        with open(filename, 'w') as file:
            file.write(yaml_data)
        
        return yaml_data

# Example 
input = {"type": "restart-kubernetes",
         "service": "webapp",
         "name": "my-webapp",
         "config": {
             "webapp_service_url":"webapp.com"
         }}
experiment = ChaosExperiment()
experiment.create(input)
experiment_yaml = experiment.generate_yaml()
print(experiment_yaml)