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
# from . import grid3D
from . import grid2D


def distManhattan(p1, p2):
    """ calcule la distance de Manhattan entre le tuple 
        p1 et le tuple p2
        """
    if len(p1) == 3:
        (x1, y1, t1) = p1
    else:
        (x1, y1) = p1
    if len(p2) == 3:
        (x2, y2, t2) = p2
    else:
        (x2, y2) = p2
    return abs(x1 - x2) + abs(y1 - y2)
    # (x1, y1) = p1
    # (x2, y2) = p2
    # return abs(x1 - x2) + abs(y1 - y2)


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
        nouveaux_fils = []
        for s in p.successeurs(self.etat):
            new_f = self.g + p.cost(self.etat, s)
            n = Noeud(s, new_f, self)
            nouveaux_fils.append(n)
        # nouveaux_fils = [Noeud(s, self.g + p.cost(self.etat, s), self) for s in p.successeurs(self.etat)]
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
    print("temps de calcul A*:", time.time() - startTime)
    n = bestNoeud
    path = []
    while n != None:
        path.append(n.etat)
        n = n.pere
    return path[::-1]  # extended slice notation to reverse list


###############################################################################
# AUTRES ALGOS DE RESOLUTIONS...
###############################################################################

# Breadth First Search
# -------------------------------

def breadthFS(p):
    """
        application de l'algorithme Breadth First Search
        sur un probleme donné
            """
    startTime = time.time()
    nodeInit = Noeud(p.init, 0, None)
    frontiere = [nodeInit]
    reserve = {}
    current = nodeInit
    while frontiere != [] and not p.estBut(current.etat):  # current != objectif:
        current = frontiere.pop(0)
        if p.immatriculation(current.etat) not in reserve:
            reserve[p.immatriculation(current.etat)] = current.g  # maj de reserve
            nextNode = current.expand(p)
            for n in nextNode:
                frontiere.append(n)
    print("temps de calcul BreadthFS:", time.time() - startTime)
    n = current
    path = []
    while n is not None:
        path.append(n.etat)
        n = n.pere
    return path[::-1]  # extended slice notation to reverse list


# Greedy-Best First
# -------------------------------

def greedyBF(p):
    """
        application de l'algorithme Greedy Best First
        sur un probleme donné
            """
    startTime = time.time()
    nodeInit = Noeud(p.init, 0, None)
    objectif = p.but
    frontiere = [(p.h_value(nodeInit.etat, objectif), nodeInit)]
    reserve = {}
    current = nodeInit
    while frontiere != [] and not p.estBut(current.etat):  # current != objectif:
        (min_h, current) = heapq.heappop(frontiere)  # node closest to objectif

        if p.immatriculation(current.etat) not in reserve:
            reserve[p.immatriculation(current.etat)] = current.g  # maj de reserve
            new = current.expand(p)
            for n in new:
                h = p.h_value(n.etat, objectif)
                heapq.heappush(frontiere, (h, n))
    print("temps de calcul GreedyBF:", time.time() - startTime)
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

def recalculateCoop3(player, team, i, g, reservation, max_t):
    path = team[player]
    curr = (path[i - 1][0], path[i - 1][1], i - 1)
    obj = path[-1]
    p = grid2D.ProblemeGrid3D(curr, obj, g, 'manhattan')
    for t in range(i + 1, len(path)):
        for x, y in path:
            reservation[(x, y, t)] = True
    new_path = coopAstar3(p, reservation, max_t)
    path[i - 1:] = new_path
    team.update({player: path})


def recalculate(algo, player, team, curr, g):
    """
        calcul d'un chemin
        """
    path = team[player]
    print("Old path :", path)
    objectif = path[-1]
    p = grid2D.ProblemeGrid2D(path[curr - 1], objectif, g, 'manhattan')
    p3 = grid2D.ProblemeGrid3D(path[curr - 1], objectif, g, 'manhattan')
    if algo == 0:
        new_path = greedyBF(p)
    elif algo == 1:
        new_path = breadthFS(p)
    else:  # by default
        new_path = astar(p)
    path[curr - 1:] = new_path
    print("New path recalculated:", path)

    team.update({player: path})


# -------------------------------
# Local-repair
# -------------------------------

def path_slicing(algo, M, player, team, curr, g):
    """
    calcul d'une partie d'un chemin
        """
    path = team[player]
    if len(path) <= curr + M:
        recalculate(algo, player, team, curr, g)
    else:
        print("Old path :", path)
        obj = path[curr + M]
        p = grid2D.ProblemeGrid2D(path[curr - 1], obj, g, 'manhattan')
        if algo == 0:
            new_path_splice = greedyBF(p)
        elif algo == 1:
            new_path_splice = breadthFS(p)
        else:  # by default
            new_path_splice = astar(p)
        path[curr - 1: curr + M + 1] = new_path_splice
        print("New path with splice :", path)
        team.update({player: path})
        # print(path)


# -------------------------------
# Factorised
# -------------------------------


def collision_checking(algo, colCheck, player, team, curr, g, ):
    """
    which alg to use how to handle collisions
        """
    if colCheck == 0:
        recalculate(algo, player, team, curr, g)

    if colCheck == 1:
        M = 4
        print("path splicing")
        path_slicing(algo, M, player, team, curr, g)


def coopAstar3(p, reservation, i):
    """
    application de l'algorithme a-star cooperatif
    sur un probleme donné
        """
    startTime = time.time()
    (x, y, t) = p.init  # [0], p.init[1], 0
    nodeInit = Noeud((x, y, t), 0, None)
    frontiere = [(nodeInit.g + p.h_value(nodeInit.etat, p.but), nodeInit)]
    reserve = {}
    bestNoeud = nodeInit
    # print("init :", bestNoeud.etat)
    it = 0
    res = []
    # res = [x for x in reservation.keys() if not reservation[x]]
    while frontiere != [] and not p.estBut(bestNoeud.etat):
        it += 1
        # print("passes the while", it)
        (min_f, bestNoeud) = heapq.heappop(frontiere)

        if bestNoeud.etat[2] >= i:
            bestNoeud = nodeInit

        if bestNoeud.pere is not None:
            (x, y, t) = bestNoeud.etat
            (x1, y1, t1) = bestNoeud.pere.etat

            # if x == x1 and y == y1 and t+1 < i:
            #     l1 = not p.estDehors((x, y-1, t)) and reservation[(x, y-1, t+1)]
            #     l2 = not p.estDehors((x, y+1, t)) and reservation[(x, y+1, t+1)]
            #     l3 = not p.estDehors((x-1, y, t)) and reservation[(x-1, y, t+1)]
            #     l4 = not p.estDehors((x+1, y, t)) and reservation[(x+1, y, t+1)]
            #
            #     if l1 or l2 or l3 or l4:
            #         n = Noeud((x, y, t+1), bestNoeud.g, bestNoeud)
            #         res.append(n)
            #         # res[n] = False
            #         # reservation[(x, y, t + 1)] = False  # pas de pause possible after 2 tours
            #     # else:
            #     #     return []

            if not reservation[(x, y, t - 1)] and not reservation[(x1, y1, t1 + 1)]:  # avoid switching positions
                continue

        # if bestNoeud not in res:
            # print("not in res")
            # print(res)
        # if bestNoeud in res:
        #     continue

        if bestNoeud == nodeInit or reservation[bestNoeud.etat]:  # if free
            if p.estBut(bestNoeud.etat):  # to avoid after teammate has stopped
                curr_t = bestNoeud.etat[2]
                for t in range(curr_t + 1, i):
                    newState = (bestNoeud.etat[0], bestNoeud.etat[1], t)
                    reservation[newState] = False

            if p.immatriculation(bestNoeud.etat) not in reserve:
                # print("bestNoeud :", bestNoeud.etat)
                reserve[p.immatriculation(bestNoeud.etat)] = bestNoeud.g  # maj de reserve
                nouveauxNoeuds = bestNoeud.expand(p)
                for n in nouveauxNoeuds:
                    # print("newNoeud to check:", n.etat)
                    f = n.g + p.h_value(n.etat, p.but)
                    heapq.heappush(frontiere, (f, n))
        # else:
        #     bestNoeud = nodeInit
    print("temps de calcul A* cooperatif :", time.time() - startTime)

    n = bestNoeud
    path = []
    while n is not None:
        reservation[n.etat] = False
        path.append((n.etat[0], n.etat[1]))
        n = n.pere

    # for i in range(len(path) - 2):
    #     if path[1]

    return path[::-1]

# cooperative : in case of future collisions we can :
#       wait for the next turn (and need to determine which agent will move first
#       recalculate the path to contourner the collision position
#       do both? check the time/heuristic w the recalculated f vs original f + wait time

#       welp,, CA* : during the prep time we assign each agent a path that has been coordinated w
#       the other (agents) paths of the team
#           how tho? do we go first agent has the path then we check each subsequent agent's path against that first?
#           or do we calculate each best path and then pit them agaisnt one another one at a time and choose the most
#           efficient?
