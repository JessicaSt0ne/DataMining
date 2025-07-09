# src/fp_growth_optimized.py

class HybridTreeNode:
    _node_id_counter = 0 

    def __init__(self, parentNode):
        self.parent = parentNode
        self.children = {}
        self.node_links_for_items = {} # item_name -> next_node_in_chain_for_this_item
        self.count = 0
        self.is_sequence_node = False
        self.item_name = None       # For single item nodes
        self.item_sequence = []     # For sequence nodes
        
        self.nid = HybridTreeNode._node_id_counter 
        HybridTreeNode._node_id_counter += 1

    def inc(self, numOccur):
        self.count += numOccur

    def get_first_item(self):
        if self.is_sequence_node:
            return self.item_sequence[0] if self.item_sequence else None
        return self.item_name

    def get_representation(self): 
        if self.is_sequence_node:
            str_sequence = [str(item) for item in self.item_sequence]
            return f"SEQ:{'-'.join(str_sequence) if str_sequence else '[]'}"
        return str(self.item_name) if self.item_name is not None else "NoneItem"

    def get_next_in_chain(self, item_name_in_chain):
        return self.node_links_for_items.get(item_name_in_chain)

    def set_next_in_chain(self, item_name_in_chain, next_node):
        self.node_links_for_items[item_name_in_chain] = next_node

    def clear_specific_link(self, item_name_in_chain):
        if item_name_in_chain in self.node_links_for_items:
            del self.node_links_for_items[item_name_in_chain]
            
    def get_all_items_represented(self):
        if self.is_sequence_node:
            return set(self.item_sequence)
        elif self.item_name and self.item_name != 'Null Set Root':
            return {self.item_name}
        return set()


    def disp(self, ind=1, item_context_for_nl=None):
        nl_repr_list = []
        if self.node_links_for_items:
            for item, next_node in self.node_links_for_items.items():
                if next_node: # Only show if there is a next node in the chain for this item
                    nl_repr_list.append(f"NL({item})->{next_node.get_representation()}(id:{next_node.nid})")
        nl_final_repr = " ".join(nl_repr_list) if nl_repr_list else ""

        print('  ' * ind, f"{self.get_representation()} (cnt:{self.count}, id:{self.nid}, parent_id:{self.parent.nid if self.parent else 'N/A'}) {nl_final_repr}")
        for child_key, child_node in sorted(self.children.items()): 
            child_node.disp(ind + 1, item_context_for_nl)

def _count_tree_nodes_optimized(node):
    if node is None:
        return 0
    count = 1 # Count current node
    for child in node.children.values():
        count += _count_tree_nodes_optimized(child)
    return count


# --- Helper: Safely remove a node from a specific item's chain ---
def _remove_node_from_chain(node_to_remove, item_in_chain, header_table):
    # print(f"      Attempting to remove '{node_to_remove.get_representation()}(id:{node_to_remove.nid})' from item '{item_in_chain}' chain.")
    if not header_table.get(item_in_chain):
        return # Item not in header table

    head_of_chain = header_table[item_in_chain][1]

    if head_of_chain == node_to_remove: # Node to remove is the head
        header_table[item_in_chain][1] = node_to_remove.get_next_in_chain(item_in_chain)
        # print(f"        Removed as head. New head for '{item_in_chain}': {header_table[item_in_chain][1].get_representation() if header_table[item_in_chain][1] else 'None'}")
    else: # Node is in the middle or tail
        current = head_of_chain
        prev = None
        visited_in_remove = set()
        while current is not None and current != node_to_remove:
            if current.nid in visited_in_remove : # safety break
                # print(f"ERROR: Loop detected in _remove_node_from_chain for {item_in_chain} at {current.nid}")
                return
            visited_in_remove.add(current.nid)
            prev = current
            current = current.get_next_in_chain(item_in_chain)
        
        if current == node_to_remove: # Found the node
            if prev is not None:
                prev.set_next_in_chain(item_in_chain, node_to_remove.get_next_in_chain(item_in_chain))
                # print(f"        Removed from mid/tail. Prev '{prev.get_representation()}(id:{prev.nid})' now links to '{node_to_remove.get_next_in_chain(item_in_chain).get_representation() if node_to_remove.get_next_in_chain(item_in_chain) else 'None'}' for item '{item_in_chain}'.")
            # else: should have been caught by head_of_chain == node_to_remove
    
    # Crucially, clear the link *from* the removed node for this specific chain
    node_to_remove.clear_specific_link(item_in_chain)

conditional_tree_id_optimized_global = 0
def create_tree_optimized(dataSet, minSup=1, context_info="MainTree_Opt"):
    # ... (内容与上一版基本一致, 确保disp和打印头指针表时使用get_next_in_chain)
    global conditional_tree_id_optimized_global
    current_tree_context = context_info
    if "CondTree for" in context_info:
        conditional_tree_id_optimized_global += 1
        key_for_context = context_info.split('CondTree for ')[1]
        current_tree_context = f"CondTree_Opt_{conditional_tree_id_optimized_global}_for_{key_for_context}"
    
    # print(f"\nDEBUG [OPTIMIZED CreateTree - {current_tree_context}]: Called with dataSet size {len(dataSet)}, minSup {minSup}")
    # if dataSet and len(dataSet) < 15:
    #     print(f"  Dataset for this tree: {dataSet}")

    headerTable = {}
    for trans, count in dataSet.items():
        for item in trans:
            headerTable[item] = headerTable.get(item, 0) + count
    
    # print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: Initial item counts: {dict(sorted(headerTable.items()))}")

    original_header_table_keys = set(headerTable.keys())
    headerTable = {k: v for k, v in headerTable.items() if v >= minSup}
    removed_items = original_header_table_keys - set(headerTable.keys())
    # if removed_items:
    #     print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: Items REMOVED by minSup ({minSup}): {sorted(list(removed_items))}")
    
    # print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: HeaderTable AFTER minSup ({minSup}) filtering: {dict(sorted({k:v for k,v in headerTable.items()}.items()))}")

    freqItemSet = set(headerTable.keys())
    if len(freqItemSet) == 0:
        # print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: No frequent items found after filtering. Returning None, None.")
        return None, None

    for k in headerTable:
        headerTable[k] = [headerTable[k], None]

    retTree = HybridTreeNode(None)
    retTree.item_name = 'Null Set Root' 
    retTree.is_sequence_node = False
    # print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: Created Root Node (id:{retTree.nid})")

    transaction_idx = 0
    for tranSet, count_val in dataSet.items():
        transaction_idx += 1
        localD = {}
        for item in tranSet:
            if item in freqItemSet: 
                localD[item] = headerTable[item][0] 

        if len(localD) > 0:
            orderedItems = [v[0] for v in sorted(localD.items(), key=lambda p: (p[1], p[0]), reverse=True)]
            update_tree_optimized(orderedItems, retTree, headerTable, count_val, current_tree_context, freqItemSet, 0)
    
    # print(f"--- [OPTIMIZED CreateTree - {current_tree_context}] Final FP-Tree Structure ---")
    # if retTree:
    #     retTree.disp()
    # print(f"--- [OPTIMIZED CreateTree - {current_tree_context}] Final Header Table ---")
    # if headerTable:
    #     for item_in_ht, val in sorted(headerTable.items()):
    #         node_link_chain_repr = []
    #         temp_node = val[1] 
    #         visited_node_ids_in_chain = set() 
    #         while temp_node:
    #             if temp_node.nid in visited_node_ids_in_chain:
    #                 node_link_chain_repr.append(f"LOOP_DETECTED_AT_ID_{temp_node.nid}")
    #                 break
    #             visited_node_ids_in_chain.add(temp_node.nid)
    #             node_link_chain_repr.append(f"{temp_node.get_representation()}(id:{temp_node.nid},cnt:{temp_node.count})")
    #             temp_node = temp_node.get_next_in_chain(item_in_ht)
    #         print(f"  Item '{item_in_ht}': Support={val[0]}, NodeLink Chain -> {' -> '.join(node_link_chain_repr) if node_link_chain_repr else 'None'}")
    # else:
    #     print("HeaderTable is None or Empty")
    # print(f"----------------------------------[OPTIMIZED CreateTree - {current_tree_context} END]----------------------------------")
    
    # 在 create_tree_optimized 函数的末尾，返回之前：
    # ... (原有代码) ...
    num_nodes = 0
    if retTree: # Ensure tree was actually built
        num_nodes = _count_tree_nodes_optimized(retTree)
    # print(f"  DEBUG [OPTIMIZED CreateTree - {current_tree_context}]: Total nodes in this tree: {num_nodes}") # 可选调试
    
    # print(f"----------------------------------[OPTIMIZED CreateTree - {current_tree_context} END]----------------------------------")
    # 修改返回语句以包含节点数
    return retTree, headerTable, num_nodes


def _update_header_optimized(head_of_chain_for_item, node_to_link, item_for_this_link):
    # This function appends node_to_link to the end of the chain for item_for_this_link,
    # starting from head_of_chain_for_item.
    current_tail = head_of_chain_for_item
    visited_ids_update = set()
    while current_tail.get_next_in_chain(item_for_this_link) is not None:
        if current_tail.nid in visited_ids_update:
            # print(f"ERROR: Loop detected in _update_header_optimized for item {item_for_this_link} at node {current_tail.nid}")
            return 
        visited_ids_update.add(current_tail.nid)
        current_tail = current_tail.get_next_in_chain(item_for_this_link)
    current_tail.set_next_in_chain(item_for_this_link, node_to_link)
    node_to_link.set_next_in_chain(item_for_this_link, None) # Ensure new tail is actual tail for this item

def _handle_node_link_optimized(header_table, item_to_link, node_to_be_linked, tree_context_for_debug=""):
    # print(f"    DEBUG [{tree_context_for_debug}] _handle_node_link_optimized: For item '{item_to_link}', node_to_be_linked='{node_to_be_linked.get_representation()}(id:{node_to_be_linked.nid})'")
    if item_to_link is not None and header_table.get(item_to_link): 
        if header_table[item_to_link][1] is None: 
            header_table[item_to_link][1] = node_to_be_linked
            node_to_be_linked.set_next_in_chain(item_to_link, None) # It's the head and tail
        else:
            _update_header_optimized(header_table[item_to_link][1], node_to_be_linked, item_to_link)

def update_tree_optimized(items_to_insert, current_fp_node, header_table, transaction_count, tree_context_for_debug, freqItemSet, recursion_depth=0):
    indent = "  " * recursion_depth
    # print(f"{indent}DEBUG UTO: items={items_to_insert}, current_node={current_fp_node.get_representation()}(id:{current_fp_node.nid}), tx_cnt={transaction_count}")

    if not items_to_insert:
        return

    first_item = items_to_insert[0]
    child_node = current_fp_node.children.get(first_item) 

    if child_node: # Existing child matches the first_item
        original_count_of_matched_child_before_inc = child_node.count # Store for potential suffix
        child_node.inc(transaction_count)
        # print(f"{indent}  Found child: {child_node.get_representation()}(id:{child_node.nid}), new_count={child_node.count}")


        if not child_node.is_sequence_node:
            # print(f"{indent}  Child is SINGLE item. Recursively calling for: {items_to_insert[1:]}")
            update_tree_optimized(items_to_insert[1:], child_node, header_table, transaction_count, tree_context_for_debug, freqItemSet, recursion_depth + 1)
        else: # Matched child IS a sequence node.
            # print(f"{indent}  Child is SEQUENCE: {child_node.item_sequence}. Comparing with insert: {items_to_insert}")
            len_insert = len(items_to_insert)
            len_sequence_in_child = len(child_node.item_sequence) # Renamed for clarity
            common_prefix_len = 0
            while (common_prefix_len < len_insert and
                   common_prefix_len < len_sequence_in_child and
                   items_to_insert[common_prefix_len] == child_node.item_sequence[common_prefix_len]):
                common_prefix_len += 1
            
            # print(f"{indent}    CommonPrefixLen: {common_prefix_len}, SeqInChildLen: {len_sequence_in_child}, InsertLen: {len_insert}")

            if common_prefix_len == len_sequence_in_child: # Existing sequence is a prefix of or equal to insert
                # print(f"{indent}    Child SEQ is prefix of insert. Recursive call for items: {items_to_insert[common_prefix_len:]}")
                update_tree_optimized(items_to_insert[common_prefix_len:], child_node, header_table, transaction_count, tree_context_for_debug, freqItemSet, recursion_depth + 1)
            else: # SPLIT occurs: common_prefix_len < len_sequence_in_child
                  # The items_to_insert match only a part of the child_node's sequence, or diverge at common_prefix_len.
                # print(f"{indent}    >>> SPLIT Occurs for child {child_node.get_representation()}(id:{child_node.nid}) count={child_node.count} <<<")
                # print(f"{indent}      items_to_insert: {items_to_insert}, original_child_seq: {child_node.item_sequence}, common_prefix_len: {common_prefix_len}")

                original_full_sequence_of_child = list(child_node.item_sequence) # Store original sequence
                original_children_of_child = dict(child_node.children)       # Store original children

                # --- CRITICAL STEP 1: Unlink the original child_node from ALL chains it was part of ---
                # It's about to change its form (item_sequence/item_name), so its old chain participations are invalid.
                # print(f"{indent}      Unlinking original child {child_node.get_representation()}(id:{child_node.nid}) from its chains.")
                for item_in_original_child_seq in original_full_sequence_of_child:
                    if item_in_original_child_seq in freqItemSet:
                         _remove_node_from_chain(child_node, item_in_original_child_seq, header_table)
                child_node.node_links_for_items = {} # Clear all its own outgoing links for all items


                # --- CRITICAL STEP 2: Morph child_node into the prefix_node ---
                # The count of child_node (now prefix_node) remains its current incremented value,
                # as transaction_count transactions DO pass through this common prefix.
                child_node.item_sequence = original_full_sequence_of_child[:common_prefix_len]
                child_node.children = {} # Prefix node will get new children (suffix and/or new branch)
                
                # print(f"{indent}      Morphed child_node to prefix: {child_node.get_representation()}(id:{child_node.nid}), new_seq: {child_node.item_sequence}")

                if len(child_node.item_sequence) == 1: # Prefix became a single item
                    child_node.item_name = child_node.item_sequence[0]
                    child_node.is_sequence_node = False
                    child_node.item_sequence = [] 
                    # print(f"{indent}      Prefix node is now SINGLE: {child_node.item_name}")
                    if child_node.item_name in freqItemSet:
                        _handle_node_link_optimized(header_table, child_node.item_name, child_node, tree_context_for_debug)
                elif not child_node.item_sequence: 
                    # This case: common_prefix_len must have been 0.
                    # This means items_to_insert[0] (first_item) matched child_node.get_first_item(),
                    # but child_node.item_sequence was longer.
                    # If common_prefix_len is 0, it means the very first item of items_to_insert
                    # did not match the first item of child_node.item_sequence. This contradicts
                    # finding child_node via current_fp_node.children.get(first_item).
                    # This state should ideally not be reached if common_prefix_len logic is correct
                    # and child_node was a sequence.
                    # However, if it means the prefix part is effectively empty (e.g., split right at the start)
                    # this usually implies the child_node itself should not exist or be the parent.
                    # For safety, if sequence becomes empty, convert to single node based on what it *was*.
                    # This part needs careful review of how common_prefix_len=0 with a sequence child is possible.
                    # Let's assume common_prefix_len > 0 if child_node.is_sequence_node and was matched.
                    # If somehow item_sequence becomes empty, it implies it was split at its very root.
                    # This might need child_node to be "absorbed" or handled differently.
                    # For now, if item_sequence is empty, we make it a single node of its original first item.
                    # This is a HACK/TODO for a very specific edge case.
                    if original_full_sequence_of_child : # check if it had items
                        child_node.item_name = original_full_sequence_of_child[0]
                        child_node.is_sequence_node = False
                        # print(f"{indent}      Prefix node became EMPTY SEQ, converted to SINGLE: {child_node.item_name}")
                        if child_node.item_name in freqItemSet:
                            _handle_node_link_optimized(header_table, child_node.item_name, child_node, tree_context_for_debug)
                    # else: # Original sequence was empty, should not happen for a sequence node
                        # print(f"{indent}      ERROR: Original sequence was empty during split.")
                else: # Prefix is still a sequence (but shorter)
                    # print(f"{indent}      Prefix node is still SEQ: {child_node.item_sequence}")
                    for item_in_prefix_seq in child_node.item_sequence:
                        if item_in_prefix_seq in freqItemSet:
                            _handle_node_link_optimized(header_table, item_in_prefix_seq, child_node, tree_context_for_debug)
                

                # --- CRITICAL STEP 3: Create and link the new_suffix_node ---
                # This node represents the remainder of the original child_node's sequence.
                # Its count is original_count_of_matched_child_before_inc because the current transaction_count
                # transactions either stop at the prefix or diverge, they don't support this specific suffix continuation.
                original_suffix_items = original_full_sequence_of_child[common_prefix_len:]
                if original_suffix_items:
                    new_suffix_node = HybridTreeNode(child_node) # Parent is the (now prefix) child_node
                    new_suffix_node.is_sequence_node = True
                    new_suffix_node.item_sequence = original_suffix_items
                    new_suffix_node.count = original_count_of_matched_child_before_inc # Key for correct count
                    new_suffix_node.children = original_children_of_child # Suffix node gets original children
                    for sub_child_key, sub_child_node in new_suffix_node.children.items(): # Re-parent them
                        sub_child_node.parent = new_suffix_node
                    
                    suffix_first_item = new_suffix_node.get_first_item()
                    if suffix_first_item is not None: # Should be true if original_suffix_items is not empty
                        child_node.children[suffix_first_item] = new_suffix_node # Link suffix to prefix node
                        # print(f"{indent}      Created new_suffix_node: {new_suffix_node.get_representation()}(id:{new_suffix_node.nid}) count={new_suffix_node.count}, parent_id={child_node.nid}")
                    
                    # Link the new_suffix_node for ALL its items
                    for item_in_suffix_seq in new_suffix_node.item_sequence:
                        if item_in_suffix_seq in freqItemSet:
                             _handle_node_link_optimized(header_table, item_in_suffix_seq, new_suffix_node, tree_context_for_debug)
                # else:
                    # print(f"{indent}      No suffix items, original child fully matched by common prefix. (This path should be common_prefix_len == len_sequence_in_child)")

                # --- CRITICAL STEP 4: Insert the remainder of items_to_insert (if any) ---
                # This forms a new branch from the child_node (which is now the prefix_node).
                # The count for this new branch is transaction_count.
                items_for_new_branch = items_to_insert[common_prefix_len:]
                if items_for_new_branch:
                    # print(f"{indent}      Inserting new branch from prefix: {items_for_new_branch}")
                    update_tree_optimized(items_for_new_branch, child_node, header_table, transaction_count, tree_context_for_debug, freqItemSet, recursion_depth + 1)
                # else:
                    # print(f"{indent}      No items for new branch, items_to_insert ended at common prefix.")

    else: # No child matches first_item, create a new node (branch)
        # print(f"{indent}  No child for '{first_item}'. Creating new node.")
        new_node = HybridTreeNode(current_fp_node)
        new_node.count = transaction_count
        
        first_item_of_new_node = items_to_insert[0]
        current_fp_node.children[first_item_of_new_node] = new_node # Add to parent's children structure

        if len(items_to_insert) > 1: 
            new_node.is_sequence_node = True
            new_node.item_sequence = list(items_to_insert)
            # print(f"{indent}    Created new SEQUENCE node: {new_node.get_representation()}(id:{new_node.nid}) count={new_node.count}")
            for item_in_seq in new_node.item_sequence: 
                if item_in_seq in freqItemSet:
                    _handle_node_link_optimized(header_table, item_in_seq, new_node, tree_context_for_debug)
        else: 
            new_node.is_sequence_node = False
            new_node.item_name = first_item_of_new_node
            # print(f"{indent}    Created new SINGLE node: {new_node.get_representation()}(id:{new_node.nid}) count={new_node.count}")
            if new_node.item_name in freqItemSet:
                 _handle_node_link_optimized(header_table, new_node.item_name, new_node, tree_context_for_debug)
    # print(f"{indent}DEBUG UTO END: items={items_to_insert}, current_node={current_fp_node.get_representation()}(id:{current_fp_node.nid})")

def ascend_tree_optimized(node_whose_path_is_needed, prefix_path_list, tree_context_for_debug=""):
    # ... (内容与上一版基本一致)
    current_ascend_node = node_whose_path_is_needed.parent
    while current_ascend_node is not None and current_ascend_node.item_name != 'Null Set Root':
        if current_ascend_node.is_sequence_node:
            if current_ascend_node.item_sequence:
                for item_in_seq in reversed(current_ascend_node.item_sequence):
                    prefix_path_list.append(item_in_seq)
        else: 
            if current_ascend_node.item_name:
                 prefix_path_list.append(current_ascend_node.item_name)
        current_ascend_node = current_ascend_node.parent


def find_prefix_path_optimized(basePat, treeNode_for_basePat_chain_head, mine_context_for_debug=""):
    # ... (内容与上一版基本一致, 确保使用 get_next_in_chain(basePat) 遍历)
    # print(f"  DEBUG [OPTIMIZED FindPrefixPath - {mine_context_for_debug}]: Called for basePat='{basePat}'")
    if not treeNode_for_basePat_chain_head:
        return {}
    
    condPats = {}
    current_path_node = treeNode_for_basePat_chain_head 
    
    visited_node_ids_in_findpath = set() 

    while current_path_node is not None:
        if current_path_node.nid in visited_node_ids_in_findpath:
            # print(f"ERROR: Loop detected in find_prefix_path_optimized for basePat {basePat} at node {current_path_node.nid}")
            break 
        visited_node_ids_in_findpath.add(current_path_node.nid)

        node_count_for_path = current_path_node.count
        prefixPath = []
        
        ascend_tree_optimized(current_path_node, prefixPath, mine_context_for_debug) 
        
        if current_path_node.is_sequence_node and current_path_node.item_sequence:
            try:
                # This logic assumes basePat is an *individual item* that might be part of a sequence.
                index_of_basePat_in_seq = current_path_node.item_sequence.index(basePat)
                items_before_in_sequence = current_path_node.item_sequence[:index_of_basePat_in_seq]
                if items_before_in_sequence:
                    for item in reversed(items_before_in_sequence): 
                        prefixPath.append(item) 
            except ValueError: 
                # If basePat is not in this particular sequence node's item_sequence, it means this node
                # (which is in basePat's chain) must be a single-item node for basePat, or an error in linking.
                # If it's a single item node for basePat, no items_before_in_sequence are added, which is correct.
                pass
        
        current_path_frozenset = frozenset([]) 
        if prefixPath:
            prefixPath.reverse() 
            current_path_frozenset = frozenset(prefixPath)
        
        condPats[current_path_frozenset] = condPats.get(current_path_frozenset, 0) + node_count_for_path
        
        current_path_node = current_path_node.get_next_in_chain(basePat)
    
    # sorted_condPats_display = {tuple(sorted(list(k))):v for k,v in condPats.items()}
    # print(f"    Conditional Pattern Bases (condPats) for '{basePat}': {dict(sorted(sorted_condPats_display.items(), key=lambda x:str(x[0])))}")
    return condPats

_generated_freq_itemsets_optimized_debug_global = set()
def mine_tree_optimized(inTree, headerTable, minSup, preFix, freqItemList, recursion_depth=0):
    # ... (内容与上一版基本一致, 确保调用 find_prefix_path_optimized, create_tree_optimized)
    global _generated_freq_itemsets_optimized_debug_global 
    if recursion_depth == 0: 
        _generated_freq_itemsets_optimized_debug_global.clear()

    indent = "  " * recursion_depth
    # print(f"\n{indent}DEBUG [OPTIMIZED MineTree]: Called. Prefix: {preFix}, HeaderTable Items: {len(headerTable) if headerTable else 0}, Recursion Depth: {recursion_depth}")

    sorted_header_items = sorted(list(headerTable.keys()))

    for basePat in sorted_header_items:
        newFreqSet = preFix.copy()
        newFreqSet.add(basePat)
        
        # print(f"{indent}  Considering basePat = '{basePat}'. Current full itemset: {newFreqSet}")
        
        current_itemset_tuple = tuple(sorted(list(newFreqSet)))
        if current_itemset_tuple not in _generated_freq_itemsets_optimized_debug_global:
            freqItemList.append(newFreqSet) 
            _generated_freq_itemsets_optimized_debug_global.add(current_itemset_tuple)
            # print(f"{indent}    Added to freqItemList: {newFreqSet} (Unique total: {len(_generated_freq_itemsets_optimized_debug_global)}, List total: {len(freqItemList)})")
        # else:
            # print(f"{indent}    Skipped DUP (already generated globally): {newFreqSet}")

        mine_debug_context = f"Mining basePat '{basePat}' with prefix {preFix}"
        header_entry = headerTable.get(basePat)
        node_link_start = None
        if header_entry and len(header_entry) > 1:
            node_link_start = header_entry[1]
        
        condPathBases = find_prefix_path_optimized(basePat, node_link_start, mine_context_for_debug=mine_debug_context)
                
        cond_tree_context_set = frozenset(newFreqSet) # Use frozenset for context key consistency
        cond_tree_context = f"CondTree for {cond_tree_context_set}"
        myCondTree, myHead = create_tree_optimized(condPathBases, minSup, context_info=cond_tree_context)
        
        if myHead is not None and len(myHead) > 0:
            # print(f"{indent}  Recursive call to mine_tree_optimized for prefix {newFreqSet}, condTree has {len(myHead)} header items.")
            mine_tree_optimized(myCondTree, myHead, minSup, newFreqSet, freqItemList, recursion_depth + 1)
        # else:
            # print(f"{indent}  No further mining for basePat '{basePat}' with prefix {newFreqSet} (myHead is None or empty for conditional tree).")
    # print(f"{indent}DEBUG [OPTIMIZED MineTree]: END. Prefix: {preFix}")   