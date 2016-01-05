from dolfin import *
import os
from helpers import FrozenClass
from problem import Problem
from function_spaces import FunctionSpaces

class SolverParameters(FrozenClass):
    
    output_dir = os.curdir


class Solver(object):

    def __init__(self, parameters, problem):

        # Check inputs and attach to class instance
	if not isinstance(parameters, SolverParameters):
	    raise TypeError, "Solver requires parameters of \
			     type SolverParameters"
        else: 
	    self.parameters = parameters
	if not isinstance(problem, Problem):
	    raise TypeError, "Problem must be of type Problem"
        else:
            self.problem = problem


    @staticmethod
    def default_parameters():
        return SolverParameters()

    
    def solve(self, parameters, problem):

        # Set up the velocity functions and spaces
        function_space = FunctionSpaces()
        V = function_space.P2
        u = TrialFunction(V)
        v = TestFunction(V)
        u0 = Function(V)
        u1 = Function(V) 
	# Set up the pressure functions and spaces
        Q = function_space.P1
        p = TrialFunction(Q)
        q = TestFunction(Q)
        p1 = Function(Q)

        # Define coefficients
	k = Constant(self.problem.parameters.dt)
	f = Constant((0,0))
	nu = Constant(self.problem.parameters.viscosity)

	# Tentative velocity step
	F1 = (1/k) * inner(u-u0, v)*dx          \
	     + inner(grad(u0)*u0, v)*dx         \
	     + nu * inner(grad(u), grad(v))*dx  \
	     - inner(f, v)*dx
	a1 = lhs(F1)
	L1 = rhs(F1)
	A1 = assemble(a1)

	# Pressure update
	a2 = inner(grad(p), grad(q))*dx
	L2 = (-1./k) * div(u1) * q * dx
	A2 = assemble(a2)

	# Velocity update
	a3 = inner(u, v)*dx
	L3 = inner(u1, v)*dx - k * inner(grad(p1), v)*dx
	A3 = assemble(a3)

        # Iterate over time-steps, start at dt
        t = self.problem.parameters.dt
        while t < self.problem.parameters.finish_time:
            print 'Starting timestep at time = ', t

            # Update the pressure BC TODO assumes pressure driven
            self.problem.parameters.BC.p_in.t = t
            self.problem.parameters.BC.update()

            # Tentative velocity step
            print 'Step 1: Computing tentative velocity'
            b1 = assemble(L1)
            [bc.apply(A1, b1) for bc in bcu] # TODO fix this
            solve(A1, u1.vector(), b1, "gmres", "default")
            end()

            # Pressure update
            print 'Step 2: Updating pressure'
            b2 = assemble(L2)
            [bc.apply(A2, b2) for bc in bcp] # TODO fix this
            solve(A2, p1.vector(), b2, "gmres", prec)
            end()

	    # Velocity update
            print 'Step 3: Updating velocity'
            b3 = assemble(L3)
            [bc.apply(A3, b3) for bc in bcu]
            solve(A3, u1.vector(), b3, "gmres", "default")
            end()

            # Timestep update
            print 'Step 4: Dump and update timestep'
            writer = StateWriter(solver=self)
            writer.write(u1, p1)
            u0.assign(u1)
            t += self.problem.parameters.dt



