# -*- coding: utf-8 -*-

# Nicolas, 2021-03-05
from __future__ import absolute_import, print_function, unicode_literals

import random
import numpy as np
import sys
from itertools import chain

import pygame

from pySpriteWorld.gameclass import Game, check_init_game_done
from pySpriteWorld.spritebuilder import SpriteBuilder
from pySpriteWorld.players import Player
from pySpriteWorld.sprite import MovingSprite
from pySpriteWorld.ontology import Ontology
import pySpriteWorld.glo

from search.grid2D import ProblemeGrid2D
from search import probleme

# ---- ---- ---- ---- ---- ----
# ---- Misc                ----
# ---- ---- ---- ---- ---- ----


# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()


def init(_boardname=None):
    global player, game
    name = _boardname if _boardname is not None else 'demoMap'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 1  # frames per second
    game.mainiteration()
    player = game.player


def main():
    # for arg in sys.argv:
    iterations = 50  # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print("Iterations: ")
    print(iterations)

    init("exAdvCoopMap")

    # -------------------------------
    # Initialisation
    # -------------------------------

    nbLignes = game.spriteBuilder.rowsize
    nbCols = game.spriteBuilder.colsize

    print("lignes", nbLignes)
    print("colonnes", nbCols)

    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    score = [0] * nbPlayers

    # on localise tous les états initiaux (loc du joueur)
    # positions initiales des joueurs
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print("Init states:", initStates)

    team1 = {initStates.index(x): x for x in initStates[::2]}
    team2 = {initStates.index(x): x for x in initStates[1::2]}
    print("t1 :", team1)
    print("t2 :", team2)

    # on localise tous les objets ramassables
    # sur le layer ramassable
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    # print("Goal states:", goalStates)

    # on localise tous les murs
    # sur le layer obstacle
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]

    # print("Wall states:", wallStates)

    def legal_position(row, col):
        # une position legale est dans la carte et pas sur un mur
        return ((row, col) not in wallStates) and 0 <= row < nbLignes and 0 <= col < nbCols

    # -------------------------------
    # Attributaion aleatoire des fioles 
    # -------------------------------

    objectifs = goalStates
    if len(objectifs) < len(initStates):
        raise Exception("There is not enough goals for all the players.")
    random.shuffle(objectifs)
    # objectifs = [(0, 17), (19, 18), (19, 11), (19, 5), (0, 11), (0, 6)]
    # objectifs = [(0, 17), (19, 11), (0, 6), (19, 5), (0, 11), (19, 18)]
    # objectifs = [(0, 6), (19, 18), (0, 17), (19, 11), (19, 5), (0, 11)]
    print(objectifs)
    for o in range(len(objectifs)):
        print("Objectif joueur", o, objectifs[o])

    # -------------------------------
    # Collision-checking handling
    # -------------------------------

    colCheck = 1  # by default
    # can be different for each team !!

    # -------------------------------
    # Path recalculation
    # -------------------------------
    def recalculate(player, team, curr, g):
        path = team[player]
        objectif = path[-1]
        p = ProblemeGrid2D(path[curr - 1], objectif, g, 'manhattan')
        new_path = probleme.astar(p)
        path[curr - 1:] = new_path
        team.update({player: path})

    # -------------------------------
    # Local-repair
    # -------------------------------
    def path_slicing(M, player, team, curr, g):
        print(path)
        if len(path) <= curr + M:
            recalculate(player, team, curr, g)
        else:
            obj = path[curr + M]
            p = ProblemeGrid2D(path[curr - 1], obj, g, 'manhattan')
            new_path_splice = probleme.astar(p)
            path[curr - 1: curr + M + 1] = new_path_splice
            # print("New path with splice :", path)
            team.update({player: path})
            print(path)

    def collision_checking(player, team, curr, g):
        if colCheck == 0:
            recalculate(player, team, curr, g)

        if colCheck == 1:
            M = 4
            print("pathsplicing")
            path_slicing(M, player, team, curr, g)


    # -------------------------------
    # calcul A* pour la team1
    # -------------------------------

    g = np.ones((nbLignes, nbCols), dtype=bool)  # par defaut la matrice comprend des True
    for w in wallStates:  # putting False for walls
        g[w] = False
    for j in team1.keys():
        p = ProblemeGrid2D(initStates[j], objectifs[j], g, 'manhattan')
        team1.update({j: probleme.astar(p)})

    # -------------------------------
    # calcul A* pour la team2
    # -------------------------------

    g = np.ones((nbLignes, nbCols), dtype=bool)  # par defaut la matrice comprend des True
    for w in wallStates:  # putting False for walls
        g[w] = False
    for j in team2.keys():
        p = ProblemeGrid2D(initStates[j], objectifs[j], g, 'manhattan')
        team2.update({j: probleme.astar(p)})

    # -------------------------------
    # Boucle principale de déplacements
    # -------------------------------
    print("\nIndependent A* algorithm with collision-checking")

    print("-----------------------------------------------------------")

    posPlayers = initStates
    collisions = [p for p in posPlayers]

    for i in range(iterations):

        print("\nIteration number", i)

        # ------------ Team 1 ---------------- #
        todo = [x for x in team1.keys()]
        won = False
        for j in todo:

            path = team1[j]

            if i >= len(path):  # if player j has reached the end of their path
                continue

            row, col = path[i]

            if i != 0 and (row, col) in collisions:  # if pos = (row, col) is occupied by another player b
                block = collisions.index((row, col))  # get the player b's index

                # if j and b are in same team and pos isn't objectif of b
                if block in team1.keys() and len(team1[block]) > i:

                    # HERE # if b is at objectif AND objectif's row, col is opti in path of a, then b should move!!
                    # ==> cooperative A* ??

                    # b hasn't moved yet and b doesn't want to switch position with j
                    if team1[block][i - 1] == (row, col) and team1[block][i] != path[i - 1]:
                        todo.append(j)
                        continue

                print("\tPlayer", j, "cannot move there : player", collisions.index((row, col)), "at", (row, col),
                      "!!\n\tPlayer", j, "will recalculate...")

                # if pos is player j's objectif
                if (row, col) == objectifs[j]:
                    path[i:] = path[i - 1:]  # player j waits
                    team1.update({j: path})
                    continue

                g[(row, col)] = False

                collision_checking(j, team1, i, g)

                todo.append(j)
                continue

            posPlayers[j] = (row, col)
            collisions[j] = posPlayers[j]
            players[j].set_rowcol(row, col)
            if i == 0:
                print("\tPlayer", j, "calculates the path to go from", initStates[j], "to", objectifs[j])
            else:
                print("\tPlayer", j, "goes from", path[i - 1], "to", (row, col))
            if (row, col) == objectifs[j]:
                score[j] += 1
                print("\n---> Team 1 : player", j, "has reached their goal !\n")

            total = 0
            for p in team1.keys():
                total += score[p]

            if total == len(team1):
                won = True
                break
        if won:
            break

        # ------------ Team 2 ---------------- #
        todo = [x for x in team2.keys()]
        won = False
        for j in todo:
            path = team2[j]

            if i >= len(path):
                continue

            row, col = path[i]
            if i != 0 and (row, col) in collisions:
                block = collisions.index((row, col))

                if block in team2.keys() and len(team2[block]) > i:

                    if team2[block][i - 1] == (row, col) and team2[block][i] != path[i - 1]:
                        todo.append(j)
                        continue

                print("\tPlayer", j, "cannot move there : player", collisions.index((row, col)), "at", (row, col),
                      "!!\n\tPlayer", j, "will recalculate...")

                if (row, col) == objectifs[j]:
                    path[i:] = path[i - 1:]  # player j waits
                    team2.update({j: path})
                    continue

                g[(row, col)] = False

                collision_checking(j, team2, i, g)

                todo.append(j)
                continue

            posPlayers[j] = (row, col)
            collisions[j] = posPlayers[j]
            players[j].set_rowcol(row, col)
            if i == 0:
                print("\tPlayer", j, "calculates the path to go from", initStates[j], "to", objectifs[j])
            else:
                print("\tPlayer", j, "goes from", path[i - 1], "to", (row, col))

            if (row, col) == objectifs[j]:
                score[j] += 1
                print("\n---> Team 2 : player", j, "has reached their goal !\n")

            total = 0
            for p in team2.keys():
                total += score[p]

            if total == len(team2):
                won = True
                break
        if won:
            break

        # on passe a l'iteration suivante du jeu
        game.mainiteration()

    # ------------ Calcul des scores ---------------- #
    print()
    dm1 = 0
    sc1 = 0
    for p in team1.keys():
        if score[p] == 0:
            dm1 += probleme.distManhattan(posPlayers[p], objectifs[p])
        else:
            sc1 += 1

    dm2 = 0
    sc2 = 0
    for p in team2.keys():
        if score[p] == 0:
            dm2 += probleme.distManhattan(posPlayers[p], objectifs[p])
        else:
            sc2 += 1

    if sc1 == sc2:
        if dm1 < dm2:
            print("Team 1 has won !!")
            print("Overall distance to its objectives is", dm1, "; whereas Team 2 is", dm2)
        elif dm2 < dm1:
            print("Team 2 has won !!")
            print("Overall distance to its objectives is", dm2, "; whereas Team 1 is", dm1)
        else:
            print("It's a draw !!")
    else:
        if sc1 > sc2:
            print("Team 1 has won !!")
            if sc1 == len(team1):
                print("Team 1's players have reached all of their goals, whereas Team 2 only reached", sc2)
            else:
                print("Team 1's players have reached", sc1, "of their goals, whereas Team 2 only reached", sc2)
        else:
            print("Team 2 has won !!")
            if sc2 == len(team2):
                print("Team 2's players have reached all of their goals, whereas Team 1 only reached", sc1)
            else:
                print("Team 2's players have reached", sc2, "of their goals, whereas Team 1 only reached", sc1)

    print("scores:", score)
    pygame.quit()

    # -------------------------------


if __name__ == '__main__':
    main()
