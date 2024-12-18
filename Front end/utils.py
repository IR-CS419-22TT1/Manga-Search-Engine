import numpy as np

# ClientFactory class to manage API clients
class ClientFactory:
    def __init__(self):
        self.clients = {}
    
    def register_client(self, name, client_class):
        self.clients[name] = client_class
    
    def create_client(self, name, **kwargs):
        client_class = self.clients.get(name)
        if client_class:
            return client_class(**kwargs)
        raise ValueError(f"Client '{name}' is not registered.")
    
    
def consolidate_results(results1, results2):
    """Consolidates results from two collections based on summed distances and includes embeddings."""
    combined_results = {}

    # Add results from the first collection
    for ids, distances, embeddings in zip(results1['ids'][0], results1['distances'][0], results1['embeddings'][0]):
        combined_results[ids] = [distances, embeddings]

    # Add results from the second collection, summing distances if the ID already exists
    for ids, distances, embeddings in zip(results2['ids'][0], results2['distances'][0], results2['embeddings'][0]):
        if ids in combined_results:
            combined_results[ids][0] += distances  # Sum distances
        else:
            combined_results[ids] = [distances, embeddings]

    # Sort results by summed distances
    sorted_results = sorted(combined_results.items(), key=lambda x: x[1][0])

    # Return the top 10 results as a dictionary
    return {k: v for k, v in sorted_results[:10]}

# Define the interactive_search function
def vector_for_interactive_search(initial_query, positive_vectors, negative_vectors):
    # Positive contribution
    if positive_vectors:
        positive_sum = np.sum(positive_vectors, axis=0)
        positive_component = 0.75 * (positive_sum / len(positive_vectors))
    else:
        positive_component = 0

    # Negative contribution
    if negative_vectors:
        negative_sum = np.sum(negative_vectors, axis=0)
        negative_component = 0.25 * (negative_sum / len(negative_vectors))
    else:
        negative_component = 0

    # Calculate the new query vector
    new_query = initial_query + positive_component - negative_component
    return new_query