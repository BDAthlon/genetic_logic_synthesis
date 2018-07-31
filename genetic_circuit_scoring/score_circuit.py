import argparse
import sys
import json

class GateLogicIncorrect(Exception):

    def __init__(self, gate_id):
        self.gate_id = gate_id

    def __str__(self):
        return "Gate {} is mapped to a gate of the incorrect logic type.".format(self.gate_id)

class GateNotMapped(Exception):

    def __init__(self, gate_id):
        self.gate_id = gate_id

    def __str__(self):
        return "Gate {} is not mapped.".format(self.gate_id)

class CrossTalkDetected(Exception):

    def __init__(self, factor_id):
        self.factor_id = factor_id

    def __str__(self):
        return "Transcription factor {} is used by multiple gates.".format(self.factor_id)

class UnsupportedGateType(Exception):

    def __init__(self, gate_id, gate_type):
        self.gate_id = gate_id
        self.gate_type = gate_type

    def __str__(self):
        return "Gate {} has unrecognized type {}.".format(self.gate_id, self.gate_type)

class GeneticGate():

    def __init__(self, id, type, ymin=None, ymax=None, k=None, n=None, factors=[]):
        self.id = id
        self.type = type
        self.ymin = ymin
        self.ymax = ymax
        self.k = k
        self.n = n
        self.factors = []
        for factor in factors:
            self.factors.append(factor)
        self.tuned_parameters = {}

    def get_ymin(self):
        if 'ymin' in self.tuned_parameters:
            return self.tuned_parameters['ymin']
        elif self.ymin is not None:
            return self.ymin
        else:
            return -1

    def get_ymax(self):
        if 'ymax' in self.tuned_parameters:
            return self.tuned_parameters['ymax']
        elif self.ymax is not None:
            return self.ymax
        else:
            return -1

    def get_k(self):
        if 'k' in self.tuned_parameters:
            return self.tuned_parameters['k']
        elif self.k is not None:
            return self.k
        else:
            return -1

    def get_n(self):
        if 'n' in self.tuned_parameters:
            return self.tuned_parameters['n']
        elif self.n is not None:
            return self.n
        else:
            return -1

    def tune_promoter(self, z):
        self.tuned_parameters['ymin'] = self.ymin*z
        self.tuned_parameters['ymax'] = self.ymax*z

    def tune_rbs(self, z):
        self.tuned_parameters['k'] = self.k/z
        self.tuned_parameters['k'] = self.k/z

    def detune(self):
        self.tuned_parameters.clear()

class CircuitMapping():

    def __init__(self, library_data):
        self.gate_library = self.__load_gate_library(library_data)

        self.r_min = self.__calculate_r_min()
        self.r_max = self.__calculate_r_max()

    def map(self, mapping_data):
        self.gates = self.__load_gates(mapping_data)
        self.connections = self.__load_connections(mapping_data)

        self.inputs = mapping_data['inputs']
        self.outputs = self.__load_outputs(mapping_data)

    def score(self):
        r_min = self.__calculate_r_min()
        if self.r_min < r_min:
            r_min = self.r_min
        r_max = self.__calculate_r_max()
        if self.r_max > r_max:
            r_max = self.r_max

        mapped_inputs = self.__map_inputs(r_min, r_max)
        mapped_outputs = self.__map_outputs(mapped_inputs)

        return self.__calculate_alpha(mapped_outputs, r_min, r_max)

    def tune(self, tuning_data):
        for gate in self.gates.values():
            gate.detune()

        for gate_data in tuning_data['gates']:
            if 'promoter' in gate_data:
                gate = self.gates[gate_data['id']]
                gate.tune_promoter(gate_data['promoter'])

            if 'rbs' in gate_data:
                gate = self.gates[gate_data['id']]
                gate.tune_rbs(gate_data['rbs'])

    def __calculate_alpha(self, mapped_outputs, r_min, r_max):
        alpha = 0

        for j in range(0, len(self.outputs[0])):
            on_min = r_max
            off_max = r_min

            for i in range(1, len(self.outputs)):
                if self.outputs[i][j] == 1 and mapped_outputs[i][j] < on_min:
                    on_min = mapped_outputs[i][j]
                elif self.outputs[i][j] == 0 and mapped_outputs[i][j] > off_max:
                    off_max = mapped_outputs[i][j]

            alpha = alpha + 1 - (r_max - on_min + off_max - r_min)/(2*(r_max - r_min))

        return alpha/len(self.outputs[0])

    def __calculate_r_min(self):
        r_min = -1

        for gate in self.gate_library.values():
            if r_min < 0 or gate.get_ymin() < r_min:
                r_min = gate.get_ymin()
            
        return r_min

    def __calculate_r_max(self):
        r_max = -1

        for gate in self.gate_library.values():
            if r_max < 0 or gate.get_ymax() > r_max:
                r_max = gate.get_ymax()
            
        return r_max

    def __load_gate_library(self, library_data):
        gate_library = {}

        for gate_data in library_data['gates']:
            gate_library[gate_data['id']] = GeneticGate(gate_data['id'], gate_data['type'], 
                gate_data['ymin'], gate_data['ymax'], gate_data['k'], gate_data['n'], gate_data['factors'])

        return gate_library

    def __load_gates(self, mapping_data):
        gates = {}
        all_factors = {}

        for gate_data in mapping_data['gates']:
            if 'mapping' in gate_data:
                gate = self.gate_library[gate_data['mapping']]

                if gate_data['type'] == gate.type:
                    gates[gate_data['id']] = gate
                else:
                    raise GateLogicIncorrect(gate_data['id'])

                for factor in gate.factors:
                    if factor in all_factors:
                        raise CrossTalkDetected(factor)
                    else:
                        all_factors[factor] = factor
            elif gate_data['type'] == 'OR':
               gates[gate_data['id']] = GeneticGate(gate_data['id'], gate_data['type'])
            else:
                raise GateNotMapped(gate_data['id'])

        return gates

    def __map_inputs(self, low_input_value, high_input_value):
        mapped_inputs = []
        mapped_inputs.append([])
        for i in range(1, len(self.inputs)):
            mapped_inputs.append([])

        for inp in self.inputs[0]:
            mapped_inputs[0].append(inp)

        k = 0
        for i in range(1, len(self.inputs)):
            for k in self.inputs[i]:
                if k == 0:
                    mapped_inputs[i].append(low_input_value)
                elif k == 1:
                    mapped_inputs[i].append(high_input_value)

        return mapped_inputs

    def __map_outputs(self, mapped_inputs):
        mapped_outputs = []
        mapped_outputs.append([])
        for i in range(1, len(self.outputs)):
            mapped_outputs.append([])

        for output in self.outputs[0]:
            mapped_outputs[0].append(output)

        for i in range(1, len(mapped_inputs)):
            sink_responses = {}
            for j in range(0, len(mapped_inputs[i])):
                sink_responses[mapped_inputs[0][j]] = mapped_inputs[i][j]

            for output in mapped_outputs[0]:
                mapped_outputs[i].append(self.__calculate_sink_response(output, sink_responses))

        return mapped_outputs

    def __load_outputs(self, mapping_data):
        outputs = []
        outputs.append([])
        for i in range(1, len(mapping_data['inputs'])):
            outputs.append([])

        for output_data in mapping_data['outputs']:
            outputs[0].append(output_data)

        for i in range(1, len(mapping_data['inputs'])):
            sink_outputs = {}
            for j in range(0, len(mapping_data['inputs'][i])):
                sink_outputs[mapping_data['inputs'][0][j]] = mapping_data['inputs'][i][j]

            for output in outputs[0]:
                outputs[i].append(self.__calculate_sink_output(output, sink_outputs))

        return outputs

    def __load_connections(self, mapping_data):
        connections = {}

        for connection_data in mapping_data['connections']:
            connections[connection_data['sink']] = []

        for connection_data in mapping_data['connections']:
            connections[connection_data['sink']].append(connection_data['source'])

        return connections

    def __calculate_sink_response(self, sink, sink_responses):
        source_response = 0

        for source in self.connections[sink]:
            if source in sink_responses:
                source_response = source_response + sink_responses[source]
            else:
                source_response = source_response + self.__calculate_sink_response(source, sink_responses)

        if sink in self.gates:
            sink_responses[sink] = self.__calculate_gate_response(source_response, self.gates[sink])
        else:
            sink_responses[sink] = source_response

        return sink_responses[sink]

    def __calculate_gate_response(self, x, gate):
        if gate.type == 'OR':
            return x
        else:
            return gate.get_ymin() + (gate.get_ymax() - gate.get_ymin())/(1.0 + pow(x/gate.get_k(), gate.get_n()))

    def __calculate_sink_output(self, sink, sink_outputs):
        source_outputs = []

        for source in self.connections[sink]:
            if source in sink_outputs:
                source_outputs.append(sink_outputs[source])
            else:
                source_outputs.append(self.__calculate_sink_output(source, sink_outputs))

        if sink in self.gates:
            sink_outputs[sink] = self.__calculate_gate_output(source_outputs, self.gates[sink])
        else:
            sink_outputs[sink] = source_outputs[0]

        return sink_outputs[sink]

    def __calculate_gate_output(self, inputs, gate):
        if gate.type == "NOT":
            if inputs[0] == 0:
                return 1
            else:
                return 0
        elif gate.type == "OR":
            if inputs[0] == 1 or inputs[1] == 1:
                return 1
            else:
                return 0
        else: 
            raise UnsupportedGateType(gate.id, gate.type)

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--library')
    parser.add_argument('-m', '--mapping')
    parser.add_argument('-t', '--tuning', nargs='?', default=None)
    args = parser.parse_args(args)

    with open(args.library) as library_file:
        library_data = json.load(library_file)
    with open(args.mapping) as mapping_file:
        mapping_data = json.load(mapping_file)
    if args.tuning is not None:
        with open(args.tuning) as tuning_file:
            tuning_data = json.load(tuning_file)
    else:
        tuning_data = None

    circuit_mapping = CircuitMapping(library_data)
    circuit_mapping.map(mapping_data)

    if tuning_data is not None:
        circuit_mapping.tune(tuning_data)

    return circuit_mapping.score()

if __name__ == '__main__':
    main()