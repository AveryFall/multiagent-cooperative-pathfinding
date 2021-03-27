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
    game.fps = 2  # frames per second
    game.mainiteration()
    player = game.player


def main():
    # for arg in sys.argv:
    iterations = 13  # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print("Iterations: ")
    print(iterations)

    init()

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

    half = len(initStates)//2
    team1 = {initStates.index(x): x for x in initStates[:half]}
    team2 = {initStates.index(x): x for x in initStates[half:]}
    # print("t1 :", team1)
    # team2 = [x for x in initStates[half:]]

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
        return ((row, col) not in wallStates) and row >= 0 and row < nbLignes and col >= 0 and col < nbCols

    # -------------------------------
    # Attributaion aleatoire des fioles 
    # -------------------------------

    objectifs = goalStates
    random.shuffle(objectifs)
    # print("Objectif joueur 0", objectifs[0])
    # print("Objectif joueur 1", objectifs[1])
    # print("Objectif joueur 2", objectifs[2])
    # print("Objectif joueur 3", objectifs[3])

    # -------------------------------
    # Carte demo 
    # 2 joueurs 
    # Joueur 0: A*
    # Joueur 1: random walker
    # -------------------------------

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

        # ------------ Team 2 ---------------- #
        todo = [x for x in team1.keys()]
        won = False
        for j in todo:
            # make it so that it works if players are randomly put in teams!!! dict?
            # name player and link it to all their pos/objectives... ?
            path = team1[j]
            if i >= len(path):
                continue

            row, col = path[i]
            # what happens if row, col is objectif ???
            if i != 0 and (row, col) in collisions:  # if pos = (row, col) is occupied by another player b
                block = collisions.index((row, col))  # get the player b's index

                # if a and b are in same team and pos isn't objectif of b
                if block in team1.keys() and len(team1[block]) < i:
                    # HERE # if b is at objectif AND objectif's row, col is opti in path of a, then b should move!!
                    # ==> cooperative A* ??

                    # b hasn't moved yet and b doesn't want to switch with a
                    if team1[block][i - 1] == (row,col) and team1[block][i] != path[i-1]:
                        todo.append(j)
                        continue
                # also path slicing instead !!!!
                # then ofc CA* w no crossover at the same time
                print("\tPlayer", j, "cannot move there : player", collisions.index((row, col)), "at", (row, col),
                      "!!\n\tPlayer", j, "will recalculate...")

                g[(row, col)] = False
                p = ProblemeGrid2D(path[i - 1], objectifs[j], g, 'manhattan')
                new_path = probleme.astar(p)
                path[i-1:] = new_path
                team1.update({j: path})
                todo.append(j)
                continue
            posPlayers[j] = (row, col)
            collisions[j] = posPlayers[j]
            players[j].set_rowcol(row, col)
            print("\tPlayer", j, "goes from", path[i-1], "to", (row, col))
            if (row, col) == objectifs[j]:
                score[j] += 1
                print("\nTeam 1 : player", j, "has reached their goal !")

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
            if i != 0 and (row, col) in collisions:  # if pos = (row, col) is occupied by another player b
                block = collisions.index((row, col))   # get the player b's index

                # if a and b are in same team and pos isn't objectif of b
                if block in team2.keys() and len(team2[block]) < i:

                    # if b hasn't moved yet and b doesn't want to switch with a
                    if team2[block][i - 1] == (row,col) and team2[block][i] != path[i-1]:
                        todo.append(j)
                        continue
                print("\tPlayer", j, "cannot move there : player", collisions.index((row, col)), "at", (row, col),
                      "!!\n\tPlayer", j, "will recalculate...")
                g[(row, col)] = False
                p = ProblemeGrid2D(path[i - 1], objectifs[j], g, 'manhattan')
                new_path = probleme.astar(p)
                path[i-1:] = new_path
                team2.update({j: path})
                todo.append(j)
                continue

            posPlayers[j] = (row, col)
            collisions[j] = posPlayers[j]
            players[j].set_rowcol(row, col)

            print("\tPlayer", j, "goes from", path[i - 1], "to", (row, col))

            if (row, col) == objectifs[j]:
                score[j] += 1
                print("\nTeam 2 : player", j, "has reached their goal !")

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

    print()
    dm1 = 0
    for p in team1.keys():
        if score[p] == 0:
            dm1 += probleme.distManhattan(posPlayers[p], objectifs[p])
    dm2 = 0
    for p in team2.keys():
        if score[p] == 0:
            dm2 += probleme.distManhattan(posPlayers[p], objectifs[p])
    if dm1 < dm2:
        print("Team 1 has won !!")
        print("Overall distance to its objectives is", dm1, "; whereas Team 2 is", dm2)
    else:
        print("Team 2 has won !!")
        print("Overall distance to its objectives is", dm2, "; whereas Team 1 is", dm1)
    print("scores:", score)
    pygame.quit()

    # -------------------------------


if __name__ == '__main__':
    main()
