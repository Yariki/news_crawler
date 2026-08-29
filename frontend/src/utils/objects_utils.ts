
function hasProperty<T, K extends PropertyKey>(
    obj: T,
    prop: K
): obj is T & Record<K, unknown> {
    return obj !== null && typeof obj === 'object' && prop in obj;
}