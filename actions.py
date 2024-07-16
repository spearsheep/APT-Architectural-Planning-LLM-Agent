from javascript import require, On, Once, AsyncTask, once, off
import math

# Import the javascript libraries
mineflayer = require("mineflayer")
pathfinder = require('mineflayer-pathfinder')
vec3 = require("vec3")

class Actions:
    def __init__(self, bot, mcData, movements,playerUsername):
        self.bot = bot
        self.mcData = mcData
        self.movements = movements
        self.playerUsername = playerUsername

    def log(self, message):
        print(f"[{self.bot.username}] {message}")
    
    def setControlState(self, control, state):
        if self.bot:
            self.bot.setControlState(control, state)
        else:
            print("Bot is not created yet. Call createBot() first.")

    def move(self, direction, blocks):
        if direction not in ["forward", "back", "left", "right"]:
            print(f"Invalid move direction: {direction}")
            return

        startPosition = self.bot.entity.position.clone()
        endPosition = startPosition.clone()

        # Calculate the end position based on the direction and blocks
        if direction == "forward":
            endPosition.z -= blocks
        elif direction == "back":
            endPosition.z += blocks
        elif direction == "left":
            endPosition.x -= blocks
        elif direction == "right":
            endPosition.x += blocks

        # Call pathfinding to move to the end position
        self.pathfinding(endPosition)

    def forward(self, blocks):
        self.move("forward", blocks)

    def back(self, blocks):
        self.move("back", blocks)

    def left(self, blocks):
        self.move("left", blocks)

    def right(self, blocks):
        self.move("right", blocks)

    def jump(self, state=True):
        self.setControlState("jump", state)

    def stop(self):
        # Stops all movement
        self.setControlState("forward", False)
        self.setControlState("back", False)
        self.setControlState("left", False)
        self.setControlState("right", False)
        self.setControlState("jump", False)

    
    
    def pathfinding(self,goalPosition,findPlayer = None):
        if findPlayer == True:
            localPlayers = self.bot.players
            for player in localPlayers:
                    playerData = localPlayers[player]
                    if playerData["username"] == self.playerUsername:
                        target = localPlayers[player].entity
                        
            if not target:
                self.bot.chat("I don't see you !")
                return
            goalPosition = target.position
            self.bot.pathfinder.setGoal(pathfinder.goals.GoalNear(goalPosition.x, goalPosition.y, goalPosition.z, 1))
        else:
            self.bot.pathfinder.setGoal(pathfinder.goals.GoalNear(goalPosition.x, goalPosition.y, goalPosition.z, 1))
    

    
    def equip(self, item, destination):
        if isinstance(item, str):
            item = next((i for i in self.bot.inventory.items() if i.name == item), None)
            if not item:
                raise ValueError(f"No item named {item} in inventory")
        self.bot.equip(item, destination)


    def consume(self):
         self.bot.consume()
    
    def fish(self):
         self.bot.fish()
    
    def sleep(self,bedBlock):
         self.bot.sleep(bedBlock)
    
    def activateBlock(self,block): #  This is the same as right-clicking a block in the game. Useful for buttons, doors, etc. You must get to the block first
         self.bot.activateBlock(block)
    
    def lookAt(self,position): #  Look at the specified position. You must go near the position before you look at it. To fill bucket with water, you must lookAt first. `position` is `Vec3`
         self.bot.lookAt(position)
    
    def useOn(self,entity): # This is the same as right-clicking an entity in the game. Useful for shearing sheep, equipping harnesses, etc.
         self.bot.useOn(entity)

    def activateItem(self):
        self.bot.activateItem()



    def moveToChest(self, chestPosition): 
        self.pathfinding(chestPosition)
        chestBlock = self.bot.blockAt(chestPosition)
        if chestBlock.name != 'trapped_chest':
            self.log(f"No chest at {chestPosition}, it is {chestBlock.name}")
            return None
        return chestBlock
    
    def placeItem(self, name, position, direction):
        if not isinstance(name, str):
            raise ValueError("name for placeItem must be a string")

        itemByName = self.mcData.itemsByName[name]
        if not itemByName:
            raise ValueError(f"No item named {name}")

        item = self.bot.inventory.findInventoryItem(itemByName['id'])
        if not item:
            self.bot.chat(f"No {name} in inventory")
            return
        else:
            self.bot.chat(f"Found {name} in inventory")

        itemCount = item.count

        directionVectors = {
            "up": vec3(0, 1, 0),
            "down": vec3(0, -1, 0),
            "forward": vec3(1, 0, 0),
            "back": vec3(-1, 0, 0),
            "left": vec3(0, 0, 1),
            "right": vec3(0, 0, -1),
        }

        if direction not in directionVectors:
            raise ValueError(f"Invalid direction {direction}. Choose from 'up', 'down', 'forward', 'back', 'left', 'right'.")

        faceVector = directionVectors[direction]
        referenceBlock = None
        blockPosition = position.minus(faceVector)
        block = self.bot.blockAt(blockPosition)
        if block and block.name != "air":
            referenceBlock = block
            self.bot.chat(f"Placing {name} on {block.name}")

        if not referenceBlock:
            self.bot.chat(f"No block to place {name} on. You cannot place a floating block.")
            return

        self.pathfinding(position)
        self.equip(item, "hand")
        self.bot.placeBlock(referenceBlock, faceVector)
        self.bot.chat
        

    def mineBlock(self,name,count=1):
        blockByName = self.mcData.blocksByName[name]
        blocks = self.bot.findBlocks({
                    "matching": blockByName.id,
                    "maxDistance": 70,
                    "count": count,
                    'timeout': 1000,
                })
        targets = [self.bot.blockAt(block) for block in blocks]
        self.bot.collectBlock.collect(targets, timeout=1000)
        self.bot.chat((f"I have finished mining {name}"))
    
    def craft_item(self, name, amount):
        # Retrieve the item by name
        item = self.bot.registry.itemsByName[name]

        # Get the crafting table ID
        craftingTableID = self.bot.registry.blocksByName.crafting_table.id

        # Find the crafting table within a 32 block radius
        craftingTable = self.bot.findBlocks({
            "matching": craftingTableID,
            "maxDistance": 32,
        })

        # Pathfind to the first crafting table found
        self.pathfinding(craftingTable[0])

        # Get the block at the crafting table location
        craftingTableBlock = self.bot.blockAt(craftingTable[0])

        # Find the recipe for the item
        recipe = self.bot.recipesFor(item.id, None, amount, craftingTableBlock)[0]

        # Craft the item with a timeout of 1000ms
        self.bot.craft(recipe, amount, craftingTableBlock, timeout=1000)


    def smelt_items(self, itemName, fuelName, count):
        item = self.bot.registry.itemsByName[itemName]
        fuel = self.bot.registry.itemsByName[fuelName]
        furnaceBlock = self.bot.findBlock({
            'matching': self.bot.registry.blocksByName.furnace.id,
            'maxDistance': 32,
        })

        self.pathfinding(furnaceBlock.position)

        furnace = self.bot.openFurnace(furnaceBlock)
        for i in range(count):
            furnace.putFuel(fuel.id, None, 1)
            furnace.putInput(item.id, None, 1)
            # Wait 12 seconds for the furnace to smelt the item
            self.bot.waitForTicks(12 * 20)
            furnace.takeOutput()
        furnace.close()

    