import ssplib

inst = 10, [6, 5, 4, 3], [1, 1, 2, 4]
print(inst)

model = ssplib.arcflow.build(inst)
model.optimize()
print(model.objVal)

solution = ssplib.arcflow.extract_solution(inst, model)
print(solution)
