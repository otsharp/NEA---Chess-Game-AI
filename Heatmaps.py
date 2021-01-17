import matplotlib.pyplot as plt

pawn_value_adjustments = [
    [9, 9, 9, 9, 9, 9, 9, 9],
    [3, 3, 3.1, 3.25, 3.25, 3.1, 3, 3],
    [2.2, 2.3, 2.4, 2.7, 2.7, 2.4, 2.3, 2.2],
    [2, 2.1, 2.2, 2.4, 2.4, 2.2, 2.1, 2],
    [1.3, 1.3, 1.3, 1.5, 1.5, 1.3, 1.3, 1.3],
    [1, 1.05, 1.1, 1.2, 1.2, 1.1, 1.05, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]]

other_value_adjustments = [
    [1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1],
    [1.05, 1.2, 1.2, 1.25, 1.25, 1.2, 1.2, 1.05],
    [1.1, 1.2, 1.25, 1.35, 1.35, 1.25, 1.2, 1.1],
    [1.1, 1.25, 1.35, 1.5, 1.5, 1.35, 1.25, 1.1],
    [1.1, 1.25, 1.35, 1.5, 1.5, 1.35, 1.25, 1.1],
    [1.05, 1.1, 1.2, 1.25, 1.25, 1.2, 1.1, 1.05],
    [1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]]

pawn_value_adjustments[0] = [4, 4, 4, 4, 4, 4, 4, 4]  # to distinguish lower values more in visuals

plt.imshow(pawn_value_adjustments, cmap=plt.cm.get_cmap("hot").reversed(), interpolation="nearest")
colour_bar = plt.colorbar() # Plotting the heatmap
plt.show()

plt.imshow(other_value_adjustments, cmap=plt.cm.get_cmap("hot").reversed(), interpolation="nearest")
colour_bar = plt.colorbar() # Plotting the 2nd heatmap
plt.show()

pawn_value_adjustments = pawn_value_adjustments[::-1]
other_value_adjustments = other_value_adjustments[::-1]

for i, row in enumerate(other_value_adjustments): # Printing the array nicely formatted
    if i == 0:
        print("[", end="")
    print(str(row), end="")
    if i == len(other_value_adjustments) - 1:
        print("]", end="")
    else:
        print(",", end="")
    print()
