# src/fp_growth_standard.py (带有调试打印)

class TreeNode:
    """
    定义FP树数据结构 (标准版)
    """
    _node_id_counter = 0 # Class variable for unique IDs for debugging

    def __init__(self, nameValue, numOccur, parentNode):
        self.name = nameValue
        self.count = numOccur
        self.nodeLink = None
        self.parent = parentNode
        self.children = {}
        
        self.nid = TreeNode._node_id_counter # Assign unique ID
        TreeNode._node_id_counter += 1


    def inc(self, numOccur):
        self.count += numOccur

    def disp(self, ind=1):
        parent_name = self.parent.name if self.parent else "None"
        node_link_name = self.nodeLink.name if self.nodeLink else "None"
        print('  ' * ind, f"{self.name} (cnt:{self.count}, id:{self.nid}, parent_id:{self.parent.nid if self.parent else 'N/A'}) {'NL->'+node_link_name+'(id:'+str(self.nodeLink.nid)+')' if self.nodeLink else ''}")
        for child_key, child_node in sorted(self.children.items()): # Sort children for consistent display
            child_node.disp(ind + 1)

def _count_tree_nodes_standard(node):
    if node is None:
        return 0
    count = 1 # Count current node
    for child in node.children.values():
        count += _count_tree_nodes_standard(child)
    return count

# --- Global counter for conditional tree IDs (for debugging) ---
conditional_tree_id_standard = 0

def create_tree_standard(dataSet, minSup=1, context_info="MainTree"):
    """
    建树 (标准版)
    """
    global conditional_tree_id_standard
    current_tree_context = context_info
    if "CondTree for" in context_info: # More specific check for conditional tree context
        conditional_tree_id_standard += 1
        current_tree_context = f"CondTree_Std_{conditional_tree_id_standard}_for_{context_info.split('CondTree for ')[1]}"
    
    print(f"\nDEBUG [STANDARD CreateTree - {current_tree_context}]: Called with dataSet size {len(dataSet)}, minSup {minSup}")
    if dataSet and len(dataSet) < 15 : # Print small datasets
        print(f"  Dataset for this tree: {dataSet}")


    headerTable = {}
    for trans, count in dataSet.items():
        for item in trans:
            headerTable[item] = headerTable.get(item, 0) + count
    
    print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: Initial item counts: {dict(sorted(headerTable.items()))}")

    original_header_table_keys = set(headerTable.keys())
    headerTable = {k: v for k, v in headerTable.items() if v >= minSup}
    removed_items = original_header_table_keys - set(headerTable.keys())
    if removed_items:
        print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: Items removed by minSup ({minSup}): {sorted(list(removed_items))}")
    
    print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: HeaderTable after minSup filtering: {dict(sorted({k:v for k,v in headerTable.items()}.items()))}")


    freqItemSet = set(headerTable.keys())
    if len(freqItemSet) == 0:
        print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: No frequent items found after filtering. Returning None, None.")
        return None, None

    for k in headerTable:
        headerTable[k] = [headerTable[k], None] # [count, node_link_pointer]

    # Reset TreeNode ID counter for each new tree for consistent IDs in disp if needed for comparison
    # TreeNode._node_id_counter = 0 # Optional: if you want IDs to restart for each tree.
                                   # Keeping it global makes IDs unique across all trees in a run.
    
    retTree = TreeNode('Null Set Root', 1, None) 
    print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: Created Root Node (id:{retTree.nid})")


    transaction_idx = 0
    for tranSet, count_val in dataSet.items():
        transaction_idx += 1
        localD = {}
        for item in tranSet:
            if item in freqItemSet: # Only consider frequent items for this transaction path
                localD[item] = headerTable[item][0] # Use global frequency for ordering

        if len(localD) > 0:
            # Sort items by global frequency (headerTable count), then alphabetically for tie-breaking
            orderedItems = [v[0] for v in sorted(localD.items(), key=lambda p: (p[1], p[0]), reverse=True)]
            print(f"    DEBUG [STANDARD CreateTree - {current_tree_context} Tx#{transaction_idx}]: Inserting ordered transaction {orderedItems} (original: {list(tranSet)}, count: {count_val}) into tree (root_id:{retTree.nid})")
            update_tree_standard(orderedItems, retTree, headerTable, count_val, current_tree_context, 0)
    
    print(f"--- [STANDARD CreateTree - {current_tree_context}] Final FP-Tree Structure ---")
    if retTree:
        retTree.disp()
    else:
        print("Tree is None")
    print(f"--- [STANDARD CreateTree - {current_tree_context}] Final Header Table ---")
    if headerTable:
        for item, val in sorted(headerTable.items()):
            node_link_chain = []
            temp_node = val[1]
            while temp_node:
                node_link_chain.append(f"{temp_node.name}(id:{temp_node.nid},cnt:{temp_node.count})")
                temp_node = temp_node.nodeLink
            print(f"  Item '{item}': Support={val[0]}, NodeLink Chain -> {' -> '.join(node_link_chain) if node_link_chain else 'None'}")
    else:
        print("HeaderTable is None or Empty")
    print(f"----------------------------------[STANDARD CreateTree - {current_tree_context} END]----------------------------------")

    # 在 create_tree_standard 函数的末尾，返回之前：
    # ... (原有代码) ...
    num_nodes = 0
    if retTree: # Ensure tree was actually built
        num_nodes = _count_tree_nodes_standard(retTree)
    # print(f"  DEBUG [STANDARD CreateTree - {current_tree_context}]: Total nodes in this tree: {num_nodes}") # 可选调试

    # print(f"----------------------------------[STANDARD CreateTree - {current_tree_context} END]----------------------------------")
    # 修改返回语句以包含节点数
    return retTree, headerTable, num_nodes

def update_tree_standard(items, inTree, headerTable, count, tree_context_for_debug, recursion_depth):
    indent = "    " + "  " * recursion_depth # For update_tree_standard prints
    # print(f"{indent}DEBUG [STANDARD UpdateTree - {tree_context_for_debug}]: items={items}, inTree='{inTree.name}(id:{inTree.nid})', count={count}")
    if not items:
        return
        
    first_item = items[0]
    if first_item in inTree.children:
        # print(f"{indent}  Item '{first_item}' found in children of '{inTree.name}(id:{inTree.nid})'. Incrementing count of child '{inTree.children[first_item].name}(id:{inTree.children[first_item].nid})' by {count}.")
        inTree.children[first_item].inc(count)
    else:
        # print(f"{indent}  Item '{first_item}' NOT found in children of '{inTree.name}(id:{inTree.nid})'. Creating new node.")
        inTree.children[first_item] = TreeNode(first_item, count, inTree)
        new_child_node = inTree.children[first_item]
        # print(f"{indent}  New node created: '{new_child_node.name}(id:{new_child_node.nid}, cnt:{new_child_node.count})'")
        
        # print(f"{indent}  Updating header for '{first_item}'. Current head: {headerTable[first_item][1].name if headerTable[first_item][1] else 'None'}")
        if headerTable[first_item][1] is None:
            headerTable[first_item][1] = new_child_node
            # print(f"{indent}    Header for '{first_item}' set to new node '{new_child_node.name}(id:{new_child_node.nid})'")
        else:
            update_header_standard(headerTable[first_item][1], new_child_node)
            # print(f"{indent}    Appended new node '{new_child_node.name}(id:{new_child_node.nid})' to header chain for '{first_item}'")

    if len(items) > 1:
        update_tree_standard(items[1:], inTree.children[first_item], headerTable, count, tree_context_for_debug, recursion_depth + 1)

def update_header_standard(nodeToTest, targetNode):
    # print(f"      DEBUG [STANDARD UpdateHeader]: Traversing from '{nodeToTest.name}(id:{nodeToTest.nid})' to link target '{targetNode.name}(id:{targetNode.nid})'")
    start_node_repr = f"{nodeToTest.name}(id:{nodeToTest.nid})"
    link_count = 0
    while nodeToTest.nodeLink is not None:
        nodeToTest = nodeToTest.nodeLink
        link_count+=1
    nodeToTest.nodeLink = targetNode
    # print(f"      DEBUG [STANDARD UpdateHeader]: Linked '{targetNode.name}(id:{targetNode.nid})' after '{nodeToTest.name}(id:{nodeToTest.nid})'. Traversed {link_count} from {start_node_repr}.")


def ascend_tree_standard_iterative(node_whose_path_is_needed, prefix_path_list):
    current_ascend_node = node_whose_path_is_needed.parent
    while current_ascend_node is not None:
        if current_ascend_node.name != 'Null Set Root':
            prefix_path_list.append(current_ascend_node.name)
            current_ascend_node = current_ascend_node.parent
        else:
            break

def find_prefix_path_standard(basePat, treeNode_for_basePat, mine_context_for_debug=""):
    print(f"  DEBUG [STANDARD FindPrefixPath - {mine_context_for_debug}]: Called for basePat='{basePat}'")
    if not treeNode_for_basePat:
        print(f"    WARN: treeNode_for_basePat is None for basePat='{basePat}'. Returning empty condPats.")
        return {}
    # else:
        # print(f"    Starting from treeNode_for_basePat='{treeNode_for_basePat.name}(id:{treeNode_for_basePat.nid}, cnt:{treeNode_for_basePat.count})'")


    condPats = {}
    current_node_occurrence = treeNode_for_basePat
    path_idx = 0
    while current_node_occurrence is not None:
        # print(f"    Path Occurrence #{path_idx} for '{basePat}': Node='{current_node_occurrence.name}(id:{current_node_occurrence.nid}, cnt:{current_node_occurrence.count})'")
        prefixPath = []
        ascend_tree_standard_iterative(current_node_occurrence, prefixPath)
        # print(f"      Path from ascend_tree (before reverse): {prefixPath}")
        
        # Standard FP-Growth expects paths from root to parent-of-basePat for conditional pattern base
        # ascend_tree_standard_iterative collects [parent, grandparent, ...]
        # So, after reverse, it becomes [..., grandparent, parent]
        if prefixPath: # If not empty
            prefixPath.reverse() 
        
        # print(f"      Final prefixPath for condPats: {list(prefixPath)}, Count: {current_node_occurrence.count}")
        
        fp = frozenset(prefixPath)
        condPats[fp] = condPats.get(fp, 0) + current_node_occurrence.count
        
        current_node_occurrence = current_node_occurrence.nodeLink
        path_idx += 1
    
    print(f"    Conditional Pattern Bases (condPats) for '{basePat}': { {tuple(sorted(list(k))):v for k,v in sorted(condPats.items(), key=lambda x:str(x[0]))} }")
    return condPats

def mine_tree_standard(inTree, headerTable, minSup, preFix, freqItemList, recursion_depth=0):
    indent = "  " * recursion_depth
    print(f"\n{indent}DEBUG [STANDARD MineTree]: Called. Prefix: {preFix}, HeaderTable Items: {len(headerTable) if headerTable else 0}, Recursion Depth: {recursion_depth}")

    # Sort items by global frequency (desc), then alphabetically for tie-breaking,
    # which is a common way to process items in FP-growth to ensure determinism
    # However, the prompt implies just sorting keys, let's stick to that for now.
    # For more deterministic mining order, especially if support counts are equal:
    # sorted_header_items = sorted(headerTable.keys(), key=lambda k: (-headerTable[k][0], k)) # Sort by Sup DESC, then Name ASC
    sorted_header_items = sorted(list(headerTable.keys()))


    for basePat in sorted_header_items:
        newFreqSet = preFix.copy()
        newFreqSet.add(basePat)
        
        print(f"{indent}  Considering basePat = '{basePat}'. Current full itemset: {newFreqSet}")
        
        # Check for duplicates (More robust way than simple list check for sets)
        # This should ideally not be necessary if logic is perfect, but helps debug
        temp_frozen_set = frozenset(newFreqSet)
        already_found = False
        for existing_f_set in freqItemList:
            if temp_frozen_set == existing_f_set: # Compare frozenset with set
                already_found = True
                break
        if not already_found:
            freqItemList.append(newFreqSet) # Add as set
            print(f"{indent}    Added to freqItemList: {newFreqSet} (Total: {len(freqItemList)})")
        else:
            print(f"{indent}    Skipped duplicate (already found by comparing frozenset): {newFreqSet}")


        mine_debug_context = f"Mining basePat '{basePat}' with prefix {preFix}"
        condPathBases = find_prefix_path_standard(basePat, headerTable[basePat][1], mine_context_for_debug=mine_debug_context)
                
        # Context for conditional tree creation
        cond_tree_context = f"CondTree for {newFreqSet}"
        myCondTree, myHead = create_tree_standard(condPathBases, minSup, context_info=cond_tree_context)
        
        if myHead is not None and len(myHead) > 0:
            print(f"{indent}  Recursive call to mine_tree_standard for prefix {newFreqSet}, condTree has {len(myHead)} header items.")
            mine_tree_standard(myCondTree, myHead, minSup, newFreqSet, freqItemList, recursion_depth + 1)
        else:
            print(f"{indent}  No further mining for basePat '{basePat}' with prefix {newFreqSet} (myHead is None or empty for conditional tree).")
    print(f"{indent}DEBUG [STANDARD MineTree]: END. Prefix: {preFix}")