# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from orchestra import conducting
from orchestra import graphing
from orchestra.specs import mock as specs
from orchestra import states
from orchestra.utils import context as ctx
from orchestra.tests.unit import base


class WorkflowConductorBasicTest(base.WorkflowConductorTest):

    def _add_tasks(self, wf_graph):
        for i in range(1, 6):
            task_name = 'task' + str(i)
            wf_graph.add_task(task_name, name=task_name)

    def _add_transitions(self, wf_graph):
        for i in range(1, 5):
            wf_graph.add_transition('task' + str(i), 'task' + str(i + 1))

    def _prep_graph(self):
        wf_graph = graphing.WorkflowGraph()

        self._add_tasks(wf_graph)
        self._add_transitions(wf_graph)

        return wf_graph

    def _add_task_flows(self, conductor):
        for i in range(1, 6):
            task_name = 'task' + str(i)
            context = ctx.set_current_task(dict(), {'id': task_name, 'name': task_name})
            conductor.update_task_flow_entry(task_name, states.RUNNING, context)
            conductor.update_task_flow_entry(task_name, states.SUCCEEDED, context)

    def _prep_conductor(self):
        wf_def = {'name': 'foobar'}
        wf_spec = specs.WorkflowSpec(wf_def)
        wf_graph = self._prep_graph()

        return conducting.WorkflowConductor(wf_spec, graph=wf_graph)

    def test_serialization(self):
        conductor = self._prep_conductor()

        self._add_task_flows(conductor)

        expected_data = {
            'spec': conductor.spec.serialize(),
            'graph': conductor.graph.serialize(),
            'flow': conductor.flow.serialize()
        }

        data = conductor.serialize()

        self.assertDictEqual(data, expected_data)

        conductor = conducting.WorkflowConductor.deserialize(data)

        self.assertIsInstance(conductor.spec, specs.WorkflowSpec)
        self.assertIsInstance(conductor.graph, graphing.WorkflowGraph)
        self.assertEqual(len(conductor.graph._graph.node), 5)
        self.assertIsInstance(conductor.flow, conducting.TaskFlow)
        self.assertEqual(len(conductor.flow.sequence), 5)

    def test_get_start_tasks(self):
        conductor = self._prep_conductor()

        expected = [{'id': 'task1', 'name': 'task1'}]

        self.assertListEqual(conductor.get_start_tasks(), expected)

    def test_get_next_tasks(self):
        conductor = self._prep_conductor()

        for i in range(1, 5):
            task_name = 'task' + str(i)
            context = ctx.set_current_task(dict(), {'id': task_name, 'name': task_name})
            conductor.update_task_flow_entry(task_name, states.RUNNING, context)
            conductor.update_task_flow_entry(task_name, states.SUCCEEDED, context)

            next_task_name = 'task' + str(i + 1)
            expected = [{'id': next_task_name, 'name': next_task_name}]

            self.assertListEqual(conductor.get_next_tasks(task_name), expected)