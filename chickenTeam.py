# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DPSAgent', second = 'TANKAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########
class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        # self.maxMoves = 5
        # self.record = [] # key format like (gameState, action)
        # self.maxTime = 0.5
        # self.confident = 1.96
        # self.maxDepth = 1
        # self.win = {} # times of local wins

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'successorScore': 1.0}

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions(self.index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(gameState, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        foodLeft = len(self.getFood(gameState).asList())

        # find the nearest food
        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        todo = random.choice(bestActions)
        print 'ReflexAgent: '
        print todo
        return todo

class DPSAgent(ReflexCaptureAgent):

    def __init__(self, index):
        ReflexCaptureAgent.__init__(self, index)
        self.idleTime = 0
        self.availableFoodNum = 999

    def registerInitialState(self, gameState):
        ReflexCaptureAgent.registerInitialState(self, gameState)

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        foodList = self.getFood(successor).asList()

        features['successorScore'] = successor.getScore()

        myPos = successor.getAgentState(self.index).getPosition()
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance

        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]

        # Ghosts within range
        ghostsInRange = filter(lambda x: not x.isPacman and x.getPosition() != None, enemies)

        if len(ghostsInRange) > 0:
            ghostsPos = [ghost.getPosition() for ghost in ghostsInRange]
            closestDis = min(self.getMazeDistance(myPos, x) for x in ghostsPos )
            features['distanceToGhost'] = closestDis

        if successor.getAgentState(self.index).isPacman:
            features['isPacman'] = 1
        else:
            features['isPacman'] = 0

        return features

    def getWeights(self, gameState, action):
        if self.idleTime > 80:
            return {'successorScore': 200, 'distanceToFood': -5, 'distanceToGhost': 2, 'isPacman': 1000}
        successor = self.getSuccessor(gameState, action)
        myPos = successor.getAgentState(self.index).getPosition()
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        ghostsInRange = filter(lambda x: not x.isPacman and x.getPosition() != None, enemies)
        if len(ghostsInRange) > 0:
            positions = [agent.getPosition() for agent in ghostsInRange]
            closestPos = min(positions, key=lambda x: self.getMazeDistance(myPos, x))
            closestDist = self.getMazeDistance(myPos, closestPos)
            closest_enemies = filter(lambda x: x[0] == closestPos, zip(positions, ghostsInRange))
            for agent in closest_enemies:
                if agent[1].scaredTimer > 0:
                    return {'successorScore': 200, 'distanceToFood': -5, 'distanceToGhost': 0, 'isPacman': 0}

        return {'successorScore': 200, 'distanceToFood': -5, 'distanceToGhost': 2, 'isPacman': 0}

    # This part is monte carlo simulation
    def randomSimulation(self, depth, gameState):
        new_state = gameState.deepCopy()

        while depth > 0:

            # Get valid actions
            actions = new_state.getLegalActions(self.index)

            # The agent should not stay stop in the simulation
            actions.remove(Directions.STOP)
            current_direction = new_state.getAgentState(self.index).configuration.direction

            # The agent should not use the reverse direction during simulation
            # Remove all reverse direction in action list
            reversed_direction = Directions.REVERSE[current_direction]
            if reversed_direction in actions and len(actions) > 1:
                actions.remove(reversed_direction)

            # Randomly chooses a valid action
            a = random.choice(actions)

            # Compute new state and update depth
            new_state = self.getSuccessor(new_state, a)
            depth -= 1

        # Evaluate the final simulation state
        return self.evaluate(new_state, Directions.STOP)

    # To to improved
    def isEmptyDeadend(self, gameState, action, depth):

        if depth == 0:
            return False
        prevScore = self.getScore(gameState)
        successor = self.getSuccessor(gameState,action)
        newScore = self.getScore(successor)  # Score of successor
        if prevScore < newScore:
            return False
        # Actions available on successor, and remove unwanted actions
        actions = successor.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        reversed_direction = Directions.REVERSE[successor.getAgentState(self.index).configuration.direction]
        if reversed_direction in actions:
            actions.remove(reversed_direction)

        # If no action available, then it is deadend
        if len(actions) == 0:
            return True
        # Recursive test deadend on successor
        for a in actions:
            if not self.isEmptyDeadend(successor, a, depth - 1):
                return False
        return True

    def chooseAction(self, gameState):

        foodList = self.getFood(gameState).asList()
        myPos = gameState.getAgentState(self.index).getPosition()
        minDis = 999
        wantedFoodInfo = []
        for food in foodList:
            if self.getMazeDistance(myPos, food) < minDis:
                minDis = self.getMazeDistance(myPos, food)
                wantedFoodInfo = []
                wantedFoodInfo.append((food, minDis))
            elif self.getMazeDistance(myPos, food) == minDis:
                minDis = self.getMazeDistance(myPos, food)
                wantedFoodInfo.append((food, minDis))

        selectedInfo = random.choice(wantedFoodInfo)

        foodPos = selectedInfo[0]
        print 'Foodpos', foodPos
        minDistance = selectedInfo[1]
        availableActions = gameState.getLegalActions(self.index)

        sucList = []
        for a in availableActions:
            suc = self.getSuccessor(gameState, a)
            sucList.append((suc, a))
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        knowGhost = filter(lambda x: not x.isPacman and x.getPosition() != None, enemies)

        if len(knowGhost) == 0 and minDistance <= 2:
            for tuple2 in sucList:
                suc = tuple2[0]
                sucPos = suc.getAgentState(self.index).getPosition()
                sucToFood = self.getMazeDistance(sucPos, foodPos)
                if sucToFood < minDistance:
                    if tuple2[1] not in availableActions:
                        print '*************************'
                    return tuple2[1]


        foodNum = len(self.getFood(gameState).asList())
        if self.availableFoodNum != foodNum:
            self.availableFoodNum = foodNum
            self.idleTime = 0
        else:
            self.idleTime += 1

        if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
            self.idleTime = 0


        availableActions.remove(Directions.STOP)
        actions = []

        for a in actions:
            if not self.isEmptyDeadend(gameState, a, 5):
                actions.append(a)

        if len(actions) == 0:
            actions = availableActions

        values = []
        for a in actions:
            new_state = self.getSuccessor(gameState, a)
            value = 0
            for i in range(1, 31):
                value += self.randomSimulation(10, new_state)
            values.append(value)

        best = max(values)
        ties = filter(lambda x: x[0] == best, zip(values, actions))
        nextAction = random.choice(ties)[1]
        print "DPSAgent: "
        print nextAction
        # print time.time() - start
        return nextAction


class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)

        # find the nearest invader
        if len(invaders) > 0:
          dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
          features['invaderDistance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}


class TANKAgent(ReflexCaptureAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.availablePos = []  # positions to patrol around
        self.preFood = None  # a list of food from previous state
        self.prey = None  # position now going to
        self.field = {}  # record the probability of going to these locations

    def registerInitialState(self, gameState):
        ReflexCaptureAgent.registerInitialState(self, gameState)
        self.distancer.getMazeDistances()
        # calculate the center of width
        if self.red:
            centerW = (gameState.data.layout.width - 2)/2
        else:
            centerW = ((gameState.data.layout.width - 2)/2) + 1

        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(centerW, i):
                self.availablePos.append((centerW, i))

        while len(self.availablePos) > (gameState.data.layout.height -2)/2:
            self.availablePos.pop(0)
            self.availablePos.pop(-1)
        self.hunt(gameState)

    def hunt(self, gameState):
        """
        This method calculate the distance between TANK and the foods it is defending,
        it will then be used to calculate target
        :param gameState:
        :return:
        """
        # Get a list of foods in your side
        foodDefending = self.getFoodYouAreDefending(gameState).asList()
        sum = 0
        for pos in self.availablePos:
            closestFoodDefDis = 999
            for food in foodDefending:
                dis = self.getMazeDistance(pos, food)
                if dis < closestFoodDefDis:
                    closestFoodDefDis = dis
            if closestFoodDefDis == 0:
                closestFoodDefDis = 1

            self.field[pos] = 1.0 / float(closestFoodDefDis)
            sum += self.field[pos]
        if sum == 0:
            sum = 1
        for x in self.field.keys():
            self.field[x] = float(self.field[x]) / float(sum)

    def selectPrey(self):
        keylist = self.field.keys()
        x = random.choice(keylist)
        return x

    def chooseAction(self, gameState):

        currentFood= self.getFoodYouAreDefending(gameState).asList()

        # If you find your food is eaten, then go to the food location
        if self.preFood and len(self.preFood) < len(currentFood):
            self.hunt(gameState)

        myPos = gameState.getAgentPosition(self.index)
        if myPos == self.prey:
            self.prey = None

        # This block handles the situation that has invaders
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = filter(lambda x: x.isPacman and x.getPosition() != None, enemies)

        if len(invaders) != 0:
            # Go to closest know invader
            positions = [agent.getPosition() for agent in invaders]
            self.prey = min(positions, key = lambda x: self.getMazeDistance(myPos, x))
        elif self.preFood != None:
            # Go to the place where food was eaten if someone ate them
            foodEaten = []
            for food in self.preFood:
                if food not in currentFood:
                    foodEaten.append(food)

            if len(foodEaten) != 0:
                # index means the latest location of food eaten
                self.prey = foodEaten.pop(0)

        self.preFood = currentFood

        # No food was eaten recently, then patrol around these food
        if self.prey is None and len(currentFood) <= 4:
            loc = currentFood
            loc += self.getCapsulesYouAreDefending()
            self.prey = random.choice(loc)
        elif self.prey is None:
            self.prey = self.selectPrey()

        # Choose actions that makes agent close to target
        availableActions = gameState.getLegalActions(self.index)
        print availableActions
        legit = []
        values = []
        for act in availableActions:
            suc = self.getSuccessor(gameState, act)
            if not suc.getAgentState(self.index).isPacman and not act == Directions.STOP:
                sucLoc = suc.getAgentPosition(self.index)
                legit.append(act)
                values.append(self.getMazeDistance(sucLoc, self.prey))
        best = min(values)
        ties = filter(lambda x: x[0] == best, zip(values, legit))
        res = random.choice(ties)[1]

        print 'TANKAgent'
        print res
        return res





