import numpy

from pysc2.agents import base_agent
from pysc2.lib import actions

from pysc2.bin import valid_actions
import pysc2


class RandomBot(base_agent.BaseAgent):
    """A random agent for StarCraft."""

    def step(self, obs):
        super(RandomBot, self).step(obs)
        action_id = numpy.random.choice(obs.observation.available_actions)
        args = [[numpy.random.randint(0, size) for size in arg.sizes]
                for arg in self.action_spec.functions[action_id].args]
        return actions.FunctionCall(action_id, args)
