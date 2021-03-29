# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 09:32:05 2016

@author: nicolas
"""

import numpy as np
import copy
import heapq
from abc import ABCMeta, abstractmethod
import functools
import time
from . import grid2D


def distManhattan(p1, p2):
    """ calcule la distance de Manhattan entre le tuple 
        p1 et le tuple p2
        """
    (x1, y1) = p1
    (x2, y2) = p2
    return abs(x1 - x2) + abs(y1 - y2)


###############################################################################

class Probleme(object):
    """ On definit un probleme comme étant: 
        - un état initial
        - un état but
        - une heuristique
        """

    def __init__(self, init, but, heuristique):
        self.init = init
        self.but = but
        self.heuristique = heuristique

    @abstractmethod
    def estBut(self, e):
        """ retourne vrai si l'état e est un état but
            """
        pass

    @abstractmethod
    def cost(self, e1, e2):
        """ donne le cout d'une action entre e1 et e2, 
            """
        pass

    @abstractmethod
    def successeurs(self, etat):
        """ retourne une liste avec les successeurs possibles
            """
        pass

    @abstractmethod
    def immatriculation(self, etat):
        """ génère une chaine permettant d'identifier un état de manière unique
            """
        pass


###############################################################################

@functools.total_ordering  # to provide comparison of nodes
class Noeud:
    def __init__(self, etat, g, pere=None):
        self.etat = etat
        self.g = g
        self.pere = pere

    def __str__(self):
        # return np.array_str(self.etat) + "valeur=" + str(self.g)
        return str(self.etat) + " valeur=" + str(self.g)

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def expand(self, p):
        """ étend un noeud avec ces fils
            pour un probleme de taquin p donné
            """
        nouveaux_fils = [Noeud(s, self.g + p.cost(self.etat, s), self) for s in p.successeurs(self.etat)]
        return nouveaux_fils

    def expandNext(self, p, k):
        """ étend un noeud unique, le k-ième fils du noeud n
            ou liste vide si plus de noeud à étendre
            """
        nouveaux_fils = self.expand(p)
        if len(nouveaux_fils) < k:
            return []
        else:
            return self.expand(p)[k - 1]

    def trace(self, p):
        """ affiche tous les ancetres du noeud
            """
        n = self
        c = 0
        while n != None:
            print(n)
            n = n.pere
            c += 1
        print("Nombre d'étapes de la solution:", c - 1)
        return

    ###############################################################################


# A*
###############################################################################

def astar(p, verbose=False, stepwise=False):
    """
    application de l'algorithme a-star
    sur un probleme donné
        """

    startTime = time.time()

    nodeInit = Noeud(p.init, 0, None)
    frontiere = [(nodeInit.g + p.h_value(nodeInit.etat, p.but), nodeInit)]
    reserve = {}
    bestNoeud = nodeInit

    while frontiere != [] and not p.estBut(bestNoeud.etat):
        (min_f, bestNoeud) = heapq.heappop(frontiere)

        # VERSION 1 --- On suppose qu'un noeud en réserve n'est jamais ré-étendu
        # Hypothèse de consistence de l'heuristique

        if p.immatriculation(bestNoeud.etat) not in reserve:
            reserve[p.immatriculation(bestNoeud.etat)] = bestNoeud.g  # maj de reserve
            nouveauxNoeuds = bestNoeud.expand(p)
            for n in nouveauxNoeuds:
                f = n.g + p.h_value(n.etat, p.but)
                heapq.heappush(frontiere, (f, n))

        # TODO: VERSION 2 --- Un noeud en réserve peut revenir dans la frontière

        stop_stepwise = ""
        if stepwise == True:
            stop_stepwise = input("Press Enter to continue (s to stop)...")
            print("best", min_f, "\n", bestNoeud)
            print("Frontière: \n", frontiere)
            print("Réserve:", reserve)
            if stop_stepwise == "s":
                stepwise = False

    # Mode verbose            
    # Affichage des statistiques (approximatives) de recherche   
    # et les differents etats jusqu'au but
    if verbose:
        bestNoeud.trace(p)
        print("=------------------------------=")
        print("Nombre de noeuds explorés", len(reserve))
        c = 0
        for (f, n) in frontiere:
            if p.immatriculation(n.etat) not in reserve:
                c += 1
        print("Nombre de noeuds de la frontière", c)
        print("Nombre de noeuds en mémoire:", c + len(reserve))
        print("temps de calcul:", time.time() - startTime)
        print("=------------------------------=")

    n = bestNoeud
    path = []
    while n != None:
        path.append(n.etat)
        n = n.pere
    return path[::-1]  # extended slice notation to reverse list


###############################################################################
# AUTRES ALGOS DE RESOLUTIONS...
###############################################################################

# Greedy-Best First
# -------------------------------

def greedyBF(p):
    nodeInit = Noeud(p.init, 0, None)
    objectif = p.but
    frontiere = [(p.h_value(nodeInit.etat, objectif), nodeInit)]
    reserve = {}
    current = nodeInit
    while frontiere != [] and not p.estBut(current.etat):  # current != objectif:
        (min_h, current) = heapq.heappop(frontiere)  # node closest to objectif
        # do i need a reserve??
        # => yes lmao u def do :facepalm:

        # VERSION 1 --- On suppose qu'un noeud en réserve n'est jamais ré-étendu
        # Hypothèse de consistence de l'heuristique

        if p.immatriculation(current.etat) not in reserve:
            reserve[p.immatriculation(current.etat)] = current.g  # maj de reserve
            new = current.expand(p)
            for n in new:
                h = p.h_value(n.etat, objectif)
                heapq.heappush(frontiere, (h, n))
    n = current
    path = []
    while n != None:
        path.append(n.etat)
        n = n.pere
    return path[::-1]  # extended slice notation to reverse list

# -------------------------------
# Collision-checking handling
# -------------------------------

# can be different for each team !!

# -------------------------------
# Path recalculation
# -------------------------------

#
# def recalculate_greedy(player, team, curr, g):
#     path = team[player]
#     print("Old path greedy :", path)
#     objectif = path[-1]
#     p = grid2D.ProblemeGrid2D(path[curr - 1], objectif, g, 'manhattan')
#     new_path = greedyBF(p)
#     path[curr - 1:] = new_path
#     print("New path greedy:", path)
#     team.update({player: path})


def recalculate(algo, player, team, curr, g):
    path = team[player]
    print("Old path :", path)
    objectif = path[-1]
    p = grid2D.ProblemeGrid2D(path[curr - 1], objectif, g, 'manhattan')
    if algo == 0:
        new_path = greedyBF(p)
    else:  # by default
        new_path = astar(p)
    path[curr - 1:] = new_path
    print("New path recalculated:", path)

    team.update({player: path})


# -------------------------------
# Local-repair
# -------------------------------

def path_slicing(algo, M, player, team, curr, g):
    path = team[player]
    if len(path) <= curr + M:
        recalculate(algo, player, team, curr, g)
    else:
        print("Old path :", path)
        obj = path[curr + M]
        p = grid2D.ProblemeGrid2D(path[curr - 1], obj, g, 'manhattan')
        if algo == 0:
            new_path_splice = greedyBF(p)
        else:  # by default
            new_path_splice = astar(p)
        path[curr - 1: curr + M + 1] = new_path_splice
        print("New path with splice :", path)
        team.update({player: path})
        # print(path)


def collision_checking(algo, colCheck, player, team, curr, g):
    if colCheck == 0:
        recalculate(algo, player, team, curr, g)

    if colCheck == 1:
        M = 4
        print("pathsplicing")
        path_slicing(algo, M, player, team, curr, g)

# cooperative : in case of future collisions we can :
#       wait for the next turn (and need to determine which agent will move first
#       recalculate the path to contourner the collision position
#       do both? check the time/heuristic w the recalculated f vs original f + wait time

#       welp,, CA* : during the prep time we assign each agent a path that has been coordinated w
#       the other (agents) paths of the team
#           how tho? do we go first agent has the path then we check each subsequent agent's path against that first?
#           or do we calculate each best path and then pit them agaisnt one another one at a time and choose the most
#           efficient?
